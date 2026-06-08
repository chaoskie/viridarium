import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { usePlants } from "./usePlants";

const PLANT: Plant = {
  id: 1,
  name: "Monstera",
  species: "Monstera deliciosa",
  location_id: 3,
  acquired_on: "2026-01-15",
  pot_size_cm: 14,
  pot_material: "terracotta",
  light_level: "bright-indirect",
  notes: null,
  tags: ["rare"],
  archived: false,
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

describe("usePlants", () => {
  it("loads and exposes plants on mount (happy, AC10)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([PLANT])));

    const { result } = renderHook(() => usePlants());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.plants).toEqual([PLANT]);
    expect(result.current.error).toBeNull();
  });

  it("exposes an empty state when there are no plants (AC10)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([])));

    const { result } = renderHook(() => usePlants());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.plants).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("surfaces a human error message on a failed fetch (sad, AC10)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 500,
        json: () => Promise.resolve({}),
      } as Response),
    );

    const { result } = renderHook(() => usePlants());

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).toMatch(/error 500/i);
    expect(result.current.plants).toEqual([]);
  });

  it("reloads the list with the active filter applied (AC5/AC10)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PLANT])) // initial mount load
      .mockResolvedValueOnce(okJson([PLANT])); // filtered reload
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.reload({ q: "mons", location_id: 3 });
    });

    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/plants?q=mons&location_id=3",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("reloads the list after a create (mutation -> reload contract, AC10)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // initial mount load
      .mockResolvedValueOnce(okJson(PLANT)) // POST response
      .mockResolvedValueOnce(okJson([PLANT])); // reload after create
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.create({
        name: "Monstera",
        species: null,
        location_id: null,
        acquired_on: null,
        pot_size_cm: null,
        pot_material: null,
        light_level: null,
        notes: null,
        tags: [],
        archived: false,
      });
    });

    expect(result.current.plants).toEqual([PLANT]);
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });
});
