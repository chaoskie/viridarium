import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  createLocation,
  deleteLocation,
  fetchLocation,
  fetchLocations,
  updateLocation,
  type Location,
} from "./locations";

const SAMPLE: Location = {
  id: 1,
  name: "Greenhouse",
  notes: "south-facing",
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
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

function stubFetch(response: Response): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("locations API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("fetchLocations", () => {
    it("returns parsed locations on 200 (happy path)", async () => {
      stubFetch(okJson(200, [SAMPLE]));
      await expect(fetchLocations()).resolves.toEqual([SAMPLE]);
    });

    it("calls GET on the locations collection", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchLocations();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/locations",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("throws ApiError on a non-2xx response (sad path)", async () => {
      stubFetch(fail(500));
      await expect(fetchLocations()).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("fetchLocation", () => {
    it("returns one location on 200", async () => {
      stubFetch(okJson(200, SAMPLE));
      await expect(fetchLocation(1)).resolves.toEqual(SAMPLE);
    });

    it("calls GET on the resource path", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await fetchLocation(7);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/locations/7",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("throws ApiError on a non-2xx response", async () => {
      stubFetch(fail(404));
      await expect(fetchLocation(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("createLocation", () => {
    it("posts and parses the created location on 201", async () => {
      stubFetch(okJson(201, SAMPLE));
      await expect(
        createLocation({ name: "Greenhouse", notes: "south-facing" }),
      ).resolves.toEqual(SAMPLE);
    });

    it("sends a POST with the correct path and JSON body", async () => {
      const fetchMock = stubFetch(okJson(201, SAMPLE));
      await createLocation({ name: "Greenhouse", notes: "south-facing" });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/locations",
        expect.objectContaining({
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name: "Greenhouse", notes: "south-facing" }),
        }),
      );
    });

    it("throws ApiError on a non-2xx response (e.g. 422)", async () => {
      stubFetch(fail(422));
      await expect(
        createLocation({ name: "", notes: null }),
      ).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("updateLocation", () => {
    it("puts and parses the updated location on 200", async () => {
      stubFetch(okJson(200, SAMPLE));
      await expect(
        updateLocation(1, { name: "Greenhouse", notes: null }),
      ).resolves.toEqual(SAMPLE);
    });

    it("sends a PUT with the correct path and JSON body", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await updateLocation(3, { name: "Shed", notes: null });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/locations/3",
        expect.objectContaining({
          method: "PUT",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify({ name: "Shed", notes: null }),
        }),
      );
    });

    it("throws ApiError on a non-2xx response", async () => {
      stubFetch(fail(404));
      await expect(
        updateLocation(99, { name: "Shed", notes: null }),
      ).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("deleteLocation", () => {
    it("resolves void on 204", async () => {
      stubFetch({ ok: true, status: 204 } as Response);
      await expect(deleteLocation(1)).resolves.toBeUndefined();
    });

    it("sends a DELETE on the resource path", async () => {
      const fetchMock = stubFetch({ ok: true, status: 204 } as Response);
      await deleteLocation(5);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/locations/5",
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("throws ApiError on a non-2xx response", async () => {
      stubFetch(fail(404));
      await expect(deleteLocation(99)).rejects.toBeInstanceOf(ApiError);
    });
  });
});
