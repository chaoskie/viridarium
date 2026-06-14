import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "@/lib/api/client";
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
  cover_photo_id: null,
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

  it("archive POSTs the archive path then reloads with the retained filter (US-2.4)", async () => {
    const archived: Plant = { ...PLANT, archived: true };
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PLANT])) // initial mount load
      .mockResolvedValueOnce(okJson([PLANT])) // reload with active filter
      .mockResolvedValueOnce(okJson(archived)) // POST /archive response
      .mockResolvedValueOnce(okJson([])); // reload after archive (retained filter)
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // Establish an active filter the hook must retain across the archive.
    await act(async () => {
      await result.current.reload({ q: "mons", location_id: 3 });
    });

    await act(async () => {
      await result.current.archive(1);
    });

    // The POST hit the archive sub-resource...
    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/v1/plants/1/archive",
      expect.objectContaining({ method: "POST" }),
    );
    // ...and the follow-up reload carried the retained filter, not bare /plants.
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/plants?q=mons&location_id=3",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("unarchive POSTs the unarchive path then reloads with the retained filter (US-2.4)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // initial mount load
      .mockResolvedValueOnce(okJson([])) // reload with archived filter
      .mockResolvedValueOnce(okJson(PLANT)) // POST /unarchive response
      .mockResolvedValueOnce(okJson([])); // reload after unarchive (retained filter)
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.reload({ archived: true });
    });

    await act(async () => {
      await result.current.unarchive(1);
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      3,
      "/api/v1/plants/1/unarchive",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenLastCalledWith(
      "/api/v1/plants?archived=true",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("archive propagates ApiError when the POST fails (sad, F4)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PLANT])) // mount reload
      .mockResolvedValueOnce(failJson(500)); // POST /archive fails
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    // The hook does not trap mutation errors (JSDoc contract) -> propagates so a
    // caller/UI can surface it. archivePlant throws before the follow-up reload.
    await expect(result.current.archive(1)).rejects.toBeInstanceOf(ApiError);
  });

  it("unarchive propagates ApiError when the POST fails (sad, F5)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PLANT])) // mount reload
      .mockResolvedValueOnce(failJson(503)); // POST /unarchive fails
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePlants());
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await expect(result.current.unarchive(1)).rejects.toBeInstanceOf(ApiError);
  });
});
