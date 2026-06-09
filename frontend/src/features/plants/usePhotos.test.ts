import { act, renderHook, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Photo } from "@/lib/api/photos";

import { usePhotos } from "./usePhotos";

const PHOTO: Photo = {
  id: 10,
  plant_id: 1,
  content_type: "image/jpeg",
  size_bytes: 2048,
  is_cover: true,
  created_at: "2026-06-08T10:00:00Z",
  url: "/api/v1/plants/1/photos/10",
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

function makeFile(): File {
  return new File([new Uint8Array([0xff, 0xd8, 0xff])], "snap.jpg", {
    type: "image/jpeg",
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("usePhotos", () => {
  it("reload populates photos and clears loading/error (happy)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([PHOTO])));

    const { result } = renderHook(() => usePhotos(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.photos).toEqual([PHOTO]);
    expect(result.current.error).toBeNull();
  });

  it("exposes an empty gallery when the plant has no photos", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([])));

    const { result } = renderHook(() => usePhotos(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.photos).toEqual([]);
    expect(result.current.error).toBeNull();
  });

  it("surfaces a human error message on a failed load", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(failJson(500)));

    const { result } = renderHook(() => usePhotos(1));

    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });
    expect(result.current.error).not.toBeNull();
    expect(result.current.photos).toEqual([]);
  });

  it("upload POSTs then reloads the gallery (mutation -> reload contract)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // mount load (empty)
      .mockResolvedValueOnce(okJson(PHOTO)) // POST upload
      .mockResolvedValueOnce(okJson([PHOTO])); // reload after upload
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePhotos(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.upload(makeFile());
    });

    expect(result.current.photos).toEqual([PHOTO]);
    expect(fetchMock).toHaveBeenCalledTimes(3);
    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/plants/1/photos",
      expect.objectContaining({ method: "POST" }),
    );
  });

  it("setCover POSTs the cover sub-resource then reloads", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PHOTO])) // mount load
      .mockResolvedValueOnce(okJson(PHOTO)) // POST cover
      .mockResolvedValueOnce(okJson([PHOTO])); // reload after set-cover
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePhotos(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.setCover(10);
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/plants/1/photos/10/cover",
      expect.objectContaining({ method: "POST" }),
    );
    expect(fetchMock).toHaveBeenCalledTimes(3);
  });

  it("remove DELETEs then reloads", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([PHOTO])) // mount load
      .mockResolvedValueOnce({ ok: true, status: 204 } as Response) // DELETE
      .mockResolvedValueOnce(okJson([])); // reload after delete
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePhotos(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.remove(10);
    });

    expect(fetchMock).toHaveBeenNthCalledWith(
      2,
      "/api/v1/plants/1/photos/10",
      expect.objectContaining({ method: "DELETE" }),
    );
    expect(result.current.photos).toEqual([]);
  });

  it("surfaces the JPEG/PNG/WebP message when upload returns 415", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // mount load
      .mockResolvedValueOnce(failJson(415)); // POST upload -> 415
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePhotos(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.upload(makeFile());
    });

    expect(result.current.error).toMatch(/JPEG, PNG, or WebP/i);
  });

  it("surfaces the too-large message when upload returns 413", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson([])) // mount load
      .mockResolvedValueOnce(failJson(413)); // POST upload -> 413
    vi.stubGlobal("fetch", fetchMock);

    const { result } = renderHook(() => usePhotos(1));
    await waitFor(() => {
      expect(result.current.loading).toBe(false);
    });

    await act(async () => {
      await result.current.upload(makeFile());
    });

    expect(result.current.error).toMatch(/too large/i);
    expect(result.current.error).toMatch(/10 MB/i);
  });
});
