import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CareSchedule, CareScheduleInput } from "@/lib/api/careSchedules";

import { useCareSchedules } from "./useCareSchedules";

const WATER: CareSchedule = {
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
  interval_days: 14,
  winter_interval_days: null,
  dormancy: "winter_interval",
  enabled: true,
};

function okJson(body: unknown): Response {
  return {
    ok: true,
    status: 200,
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

describe("useCareSchedules", () => {
  it("reload populates schedules and clears loading/error (happy)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([WATER])));

    const { result } = renderHook(() => useCareSchedules(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.schedules).toEqual([WATER]);
    expect(result.current.error).toBeNull();
  });

  it("exposes an empty list when the plant has no schedules", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([])));

    const { result } = renderHook(() => useCareSchedules(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.schedules).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("surfaces a human error message on a failed load", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(failJson(500)));

    const { result } = renderHook(() => useCareSchedules(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).not.toBeNull();
    expect(result.current.schedules).toEqual([]);
  });

  it("upsert PUTs the keyed path then reloads (mutation -> reload contract)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // mount load (empty)
      .mockResolvedValueOnce(okJson({ ...WATER, interval_days: 14 })) // PUT upsert
      .mockResolvedValueOnce(okJson([{ ...WATER, interval_days: 14 }])); // reload
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCareSchedules(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.upsert("water", INPUT);
    });

    expect(result.current.schedules).toEqual([{ ...WATER, interval_days: 14 }]);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/plants/1/schedules/water",
      expect.objectContaining({ method: "PUT" }),
    );
  });

  it("remove DELETEs the keyed path then reloads", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([WATER])) // mount load
      .mockResolvedValueOnce({ ok: true, status: 204 } as Response) // DELETE
      .mockResolvedValueOnce(okJson([])); // reload after delete
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCareSchedules(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.remove("water");
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/plants/1/schedules/water",
      expect.objectContaining({ method: "DELETE" }),
    );
    expect(result.current.schedules).toEqual([]);
  });

  it("propagates a human error on a failed upsert (422)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // mount load
      .mockResolvedValueOnce(failJson(422)); // PUT upsert -> 422
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useCareSchedules(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.upsert("water", INPUT);
    });

    expect(result.current.error).not.toBeNull();
  });
});
