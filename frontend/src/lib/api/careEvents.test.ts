import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  createEvent,
  deleteEvent,
  fetchEvents,
  type CareEvent,
  type CareEventInput,
} from "./careEvents";

const SAMPLE: CareEvent = {
  id: 5,
  plant_id: 1,
  type: "water",
  happened_on: "2026-06-11",
  note: null,
  photo_id: null,
  health: null,
  created_at: "2026-06-11T10:00:00Z",
};

// Full-body input: every optional field present (the F-2 contract).
const INPUT: CareEventInput = {
  type: "observe",
  happened_on: "2026-06-10",
  note: "New leaf unfurling",
  photo_id: 10,
  health: "good",
};

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

function fail(status: number): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

function stubFetch(response: Response): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** Today's local calendar date as YYYY-MM-DD (independent oracle). */
function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

describe("careEvents API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("fetchEvents", () => {
    it("GETs the collection path with the JSON Accept header (F-1)", async () => {
      const fetchMock = stubFetch(okJson(200, [SAMPLE]));
      await expect(fetchEvents(1)).resolves.toEqual([SAMPLE]);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/events",
        expect.objectContaining({ headers: { Accept: "application/json" } }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404) (F-5)", async () => {
      stubFetch(fail(404));
      await expect(fetchEvents(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("createEvent", () => {
    it("POSTs the collection path with the JSON body (F-2)", async () => {
      const created: CareEvent = {
        ...SAMPLE,
        type: "observe",
        happened_on: "2026-06-10",
        note: "New leaf unfurling",
        photo_id: 10,
        health: "good",
      };
      const fetchMock = stubFetch(okJson(201, created));

      await expect(createEvent(1, INPUT)).resolves.toEqual(created);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(path).toBe("/api/v1/plants/1/events");
      expect(init.method).toBe("POST");
      expect(init.headers).toMatchObject({
        Accept: "application/json",
        "Content-Type": "application/json",
      });
      expect(init.body).toBe(JSON.stringify(INPUT));
    });

    it("quick-tap body carries the type and today's date only (F-3)", async () => {
      const today = localToday();
      const fetchMock = stubFetch(
        okJson(201, { ...SAMPLE, happened_on: today }),
      );

      await createEvent(1, { type: "water", happened_on: today });

      const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      const body = JSON.parse(init.body as string) as Record<string, unknown>;
      expect(body).toEqual({ type: "water", happened_on: today });
    });

    it("throws ApiError on a non-2xx response (incl. 422) (F-6)", async () => {
      stubFetch(fail(422));
      await expect(createEvent(1, INPUT)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("deleteEvent", () => {
    it("DELETEs the keyed path and resolves void on 204 (F-4)", async () => {
      const fetchMock = stubFetch({ ok: true, status: 204 } as Response);
      await expect(deleteEvent(1, 5)).resolves.toBeUndefined();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/events/5",
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404) (F-7)", async () => {
      stubFetch(fail(404));
      await expect(deleteEvent(1, 99)).rejects.toBeInstanceOf(ApiError);
    });
  });
});
