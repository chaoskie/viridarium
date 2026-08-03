import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Location } from "@/lib/api/locations";

import { useLocations } from "./useLocations";

const ROOM: Location = {
  id: 1,
  name: "Greenhouse",
  notes: null,
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

function okJson(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("useLocations", () => {
  it("loads and exposes locations on mount (happy, AC7)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([ROOM])));

    const { result } = renderHook(() => useLocations());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.locations).toEqual([ROOM]);
    expect(result.current.error).toBeNull();
  });

  it("exposes an empty state when there are no rooms (AC7)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([])));

    const { result } = renderHook(() => useLocations());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.locations).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("surfaces a human error message on a failed fetch (sad, AC7)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({}),
      }),
    );

    const { result } = renderHook(() => useLocations());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toMatch(/error 500/i);
    expect(result.current.locations).toEqual([]);
  });

  it("reloads the list after a create (mutation -> reload contract)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // initial mount load
      .mockResolvedValueOnce(okJson(ROOM)) // POST response
      .mockResolvedValueOnce(okJson([ROOM])); // reload after create
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => useLocations());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.create({ name: "Greenhouse", notes: null });
    });

    expect(result.current.locations).toEqual([ROOM]);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
