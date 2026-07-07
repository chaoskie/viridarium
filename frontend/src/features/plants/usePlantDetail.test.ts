import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { usePlantDetail } from "./usePlantDetail";

const PLANT: Plant = {
  id: 3,
  name: "Fiddle Leaf Fig",
  species: null,
  location_id: null,
  acquired_on: null,
  pot_size_cm: null,
  pot_material: null,
  outer_pot_material: null,
  outer_pot_size_cm: null,
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
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
    json: () => Promise.resolve({ detail: "nope" }),
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("usePlantDetail", () => {
  it("resolves to ready with the plant (F-1)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson(200, PLANT)));

    const { result } = renderHook(() => usePlantDetail(3));

    expect(result.current.state.kind).toBe("loading");
    await waitFor(() => {
      expect(result.current.state.kind).toBe("ready");
    });
    expect(
      result.current.state.kind === "ready" ? result.current.state.plant : null,
    ).toEqual(PLANT);
  });

  it("rejects to error (F-2)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(fail(404)));

    const { result } = renderHook(() => usePlantDetail(3));

    await waitFor(() => {
      expect(result.current.state.kind).toBe("error");
    });
  });

  it("invalid or non-positive id errors without a fetch (F-3)", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    const zero = renderHook(() => usePlantDetail(0));
    const nan = renderHook(() => usePlantDetail(Number.NaN));

    await waitFor(() => {
      expect(zero.result.current.state.kind).toBe("error");
      expect(nan.result.current.state.kind).toBe("error");
    });
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("a stale slow fetch never overwrites a newer plant's data (F-4b, race guard)", async () => {
    const slowPlant: Plant = { ...PLANT, id: 1, name: "Slow Plant" };
    const fastPlant: Plant = { ...PLANT, id: 2, name: "Fast Plant" };
    let releaseSlow: (() => void) | undefined;
    const fetchMock = vi
      .fn()
      // First call (id=1) resolves only when released, after the second.
      .mockImplementationOnce(
        () =>
          new Promise<Response>((resolve) => {
            releaseSlow = () => {
              resolve(okJson(200, slowPlant));
            };
          }),
      )
      .mockResolvedValueOnce(okJson(200, fastPlant));
    vi.stubGlobal("fetch", fetchMock);

    const { result, rerender } = renderHook(
      ({ id }: { id: number }) => usePlantDetail(id),
      { initialProps: { id: 1 } },
    );

    rerender({ id: 2 });
    await waitFor(() => {
      expect(result.current.state.kind).toBe("ready");
    });

    await act(async () => {
      releaseSlow?.();
      await Promise.resolve();
    });

    expect(
      result.current.state.kind === "ready"
        ? result.current.state.plant.name
        : null,
    ).toBe("Fast Plant");
  });

  it("reload() refetches and exposes fresh data (F-4)", async () => {
    const updated: Plant = { ...PLANT, cover_photo_id: 9 };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(200, PLANT))
      .mockResolvedValueOnce(okJson(200, updated));
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlantDetail(3));

    await waitFor(() => {
      expect(result.current.state.kind).toBe("ready");
    });

    await act(async () => {
      await result.current.reload();
    });

    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(
      result.current.state.kind === "ready"
        ? result.current.state.plant.cover_photo_id
        : null,
    ).toBe(9);
  });
});
