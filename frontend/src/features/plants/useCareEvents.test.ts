import { act, renderHook } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CareEvent } from "@/lib/api/careEvents";

import { useCareEvents } from "./useCareEvents";

const CREATED: CareEvent = {
  id: 5,
  plant_id: 1,
  type: "water",
  happened_on: "2026-06-11",
  note: null,
  photo_id: null,
  health: null,
  created_at: "2026-06-11T10:00:00Z",
};

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

function failJson(status: number): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useCareEvents", () => {
  it("log POSTs the event and returns the created row (happy)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(okJson(201, CREATED));
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCareEvents(1));

    let created: CareEvent | null = null;
    await act(async () => {
      created = await result.current.log({
        type: "water",
        happened_on: "2026-06-11",
      });
    });

    expect(created).toEqual(CREATED);
    expect(result.current.error).toBeNull();
    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/plants/1/events",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("log traps a failure into a human error and returns null (sad)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(failJson(500)));

    const { result } = renderHook(() => useCareEvents(1));

    let created: CareEvent | null = CREATED;
    await act(async () => {
      created = await result.current.log({ type: "feed" });
    });

    expect(created).toBeNull();
    expect(result.current.error).not.toBeNull();
  });

  it("a successful log clears the previous error", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(failJson(422))
      .mockResolvedValueOnce(okJson(201, CREATED));
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCareEvents(1));

    await act(async () => {
      await result.current.log({ type: "water" });
    });
    expect(result.current.error).not.toBeNull();

    await act(async () => {
      await result.current.log({ type: "water" });
    });
    expect(result.current.error).toBeNull();
  });
});
