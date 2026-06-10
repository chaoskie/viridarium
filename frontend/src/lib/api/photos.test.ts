import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  deletePhoto,
  fetchPhotos,
  photoUrl,
  setCoverPhoto,
  uploadPhoto,
  type Photo,
} from "./photos";

const SAMPLE: Photo = {
  id: 10,
  plant_id: 1,
  content_type: "image/jpeg",
  size_bytes: 2048,
  is_cover: true,
  created_at: "2026-06-08T10:00:00Z",
  url: "/api/v1/plants/1/photos/10",
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

/** A tiny real `File` (jsdom provides the constructor). */
function makeFile(): File {
  return new File([new Uint8Array([0xff, 0xd8, 0xff])], "snap.jpg", {
    type: "image/jpeg",
  });
}

describe("photos API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("uploadPhoto", () => {
    it("posts a FormData body whose `file` field is the given File", async () => {
      const fetchMock = stubFetch(okJson(201, SAMPLE));
      const file = makeFile();

      await uploadPhoto(1, file);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(path).toBe("/api/v1/plants/1/photos");
      expect(init.method).toBe("POST");
      expect(init.body).toBeInstanceOf(FormData);
      expect((init.body as FormData).get("file")).toBe(file);
    });

    it("does NOT set a Content-Type header (browser sets the multipart boundary)", async () => {
      const fetchMock = stubFetch(okJson(201, SAMPLE));

      await uploadPhoto(1, makeFile());

      const [, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      const headers = (init.headers ?? {}) as Record<string, string>;
      // The boundary is browser-generated; a manual Content-Type breaks it.
      expect(headers).not.toHaveProperty("Content-Type");
      expect(headers).not.toHaveProperty("content-type");
      // Accept is still negotiated.
      expect(headers).toMatchObject({ Accept: "application/json" });
    });

    it("parses and returns the created Photo on 201", async () => {
      stubFetch(okJson(201, SAMPLE));
      await expect(uploadPhoto(1, makeFile())).resolves.toEqual(SAMPLE);
    });

    it("throws ApiError on a 415 / 413 (non-2xx) response", async () => {
      stubFetch(fail(415));
      await expect(uploadPhoto(1, makeFile())).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("fetchPhotos", () => {
    it("GETs the collection path with the JSON Accept header", async () => {
      const fetchMock = stubFetch(okJson(200, [SAMPLE]));
      await expect(fetchPhotos(1)).resolves.toEqual([SAMPLE]);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/photos",
        expect.objectContaining({ headers: { Accept: "application/json" } }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(fetchPhotos(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("setCoverPhoto", () => {
    it("POSTs the cover sub-resource with an empty JSON body", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await expect(setCoverPhoto(1, 10)).resolves.toEqual(SAMPLE);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/photos/10/cover",
        expect.objectContaining({
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({}),
        }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(setCoverPhoto(1, 99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("deletePhoto", () => {
    it("DELETEs the resource path and resolves void on 204", async () => {
      const fetchMock = stubFetch({ ok: true, status: 204 } as Response);
      await expect(deletePhoto(1, 10)).resolves.toBeUndefined();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/photos/10",
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(deletePhoto(1, 99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("photoUrl", () => {
    it("builds the raw-bytes URL for an <img src>", () => {
      expect(photoUrl(1, 10)).toBe("/api/v1/plants/1/photos/10");
      expect(photoUrl(42, 7)).toBe("/api/v1/plants/42/photos/7");
    });
  });
});
