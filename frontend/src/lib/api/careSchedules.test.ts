import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  deleteSchedule,
  fetchSchedules,
  upsertSchedule,
  type CareSchedule,
  type CareScheduleInput,
} from "./careSchedules";

const SAMPLE: CareSchedule = {
  plant_id: 1,
  care_type: "water",
  interval_days: 7,
  winter_interval_days: null,
  dormancy: "winter_interval",
  enabled: true,
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

const INPUT: CareScheduleInput = {
  interval_days: 7,
  winter_interval_days: null,
  dormancy: "winter_interval",
  enabled: true,
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

describe("careSchedules API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("fetchSchedules", () => {
    it("GETs the collection path with the JSON Accept header", async () => {
      const fetchMock = stubFetch(okJson(200, [SAMPLE]));
      await expect(fetchSchedules(1)).resolves.toEqual([SAMPLE]);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/schedules",
        expect.objectContaining({ headers: { Accept: "application/json" } }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(fetchSchedules(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("upsertSchedule", () => {
    it("PUTs the keyed path with the JSON body (no care_type in the body)", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));

      await expect(upsertSchedule(1, "water", INPUT)).resolves.toEqual(SAMPLE);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(path).toBe("/api/v1/plants/1/schedules/water");
      expect(init.method).toBe("PUT");
      expect(init.headers).toMatchObject({
        Accept: "application/json",
        "Content-Type": "application/json",
      });
      expect(init.body).toBe(JSON.stringify(INPUT));
      // care_type travels in the path only, never in the body (design CS1).
      expect(init.body as string).not.toContain("care_type");
    });

    it("uses the feed care_type in the keyed path", async () => {
      const fetchMock = stubFetch(
        okJson(200, { ...SAMPLE, care_type: "feed" }),
      );
      await upsertSchedule(42, "feed", { ...INPUT, interval_days: 30 });
      const [path] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(path).toBe("/api/v1/plants/42/schedules/feed");
    });

    it("throws ApiError on a non-2xx response (incl. 422)", async () => {
      stubFetch(fail(422));
      await expect(upsertSchedule(1, "water", INPUT)).rejects.toBeInstanceOf(
        ApiError,
      );
    });
  });

  describe("deleteSchedule", () => {
    it("DELETEs the keyed path and resolves void on 204", async () => {
      const fetchMock = stubFetch({ ok: true, status: 204 } as Response);
      await expect(deleteSchedule(1, "water")).resolves.toBeUndefined();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/schedules/water",
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(deleteSchedule(1, "feed")).rejects.toBeInstanceOf(ApiError);
    });
  });
});
