import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  archivePlant,
  createPlant,
  deletePlant,
  fetchPlant,
  fetchPlants,
  unarchivePlant,
  updatePlant,
  type Plant,
  type PlantInput,
} from "./plants";

const SAMPLE: Plant = {
  id: 1,
  name: "Monstera",
  species: "Monstera deliciosa",
  location_id: 3,
  acquired_on: "2026-01-15",
  pot_size_cm: 14,
  pot_material: "terracotta",
  light_level: "bright-indirect",
  notes: "north window",
  tags: ["rare", "fern"],
  archived: false,
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

const INPUT: PlantInput = {
  name: "Monstera",
  species: "Monstera deliciosa",
  location_id: 3,
  acquired_on: "2026-01-15",
  pot_size_cm: 14,
  pot_material: "terracotta",
  light_level: "bright-indirect",
  notes: "north window",
  tags: ["rare", "fern"],
  archived: false,
};

const HOMELESS_INPUT: PlantInput = {
  name: "Pothos",
  species: null,
  location_id: null,
  acquired_on: null,
  pot_size_cm: null,
  pot_material: null,
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
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

describe("plants API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("fetchPlants", () => {
    it("returns parsed plants on 200 (happy path)", async () => {
      stubFetch(okJson(200, [SAMPLE]));
      await expect(fetchPlants()).resolves.toEqual([SAMPLE]);
    });

    it("calls GET on the bare collection when no filter is given", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants();
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("builds a query string from the filter (only set fields appended)", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({
        q: "mons",
        location_id: 3,
        tag: "rare",
        species: "ficus",
      });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?q=mons&location_id=3&tag=rare&species=ficus",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("renders homeless=true in the query string", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ homeless: true });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?homeless=true",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("renders archived=true when filtering to archived only (US-2.4)", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ archived: true });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?archived=true",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("renders archived=false to scope to active only (US-2.4)", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ archived: false });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?archived=false",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("renders include_archived=true to return all plants (US-2.4)", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ include_archived: true });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?include_archived=true",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("omits include_archived when false (US-2.4)", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ include_archived: false });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("omits unset / empty filter fields from the query string", async () => {
      const fetchMock = stubFetch(okJson(200, []));
      await fetchPlants({ q: "", location_id: null, tag: "rare" });
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants?tag=rare",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("throws ApiError on a non-2xx response (sad path)", async () => {
      stubFetch(fail(422));
      await expect(fetchPlants()).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("fetchPlant", () => {
    it("returns one plant on 200", async () => {
      stubFetch(okJson(200, SAMPLE));
      await expect(fetchPlant(1)).resolves.toEqual(SAMPLE);
    });

    it("calls GET on the resource path", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await fetchPlant(7);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/7",
        expect.objectContaining({
          headers: { Accept: "application/json" },
        }),
      );
    });

    it("throws ApiError on a non-2xx response (incl. 404)", async () => {
      stubFetch(fail(404));
      await expect(fetchPlant(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("createPlant", () => {
    it("posts and parses the created plant on 201", async () => {
      stubFetch(okJson(201, SAMPLE));
      await expect(createPlant(INPUT)).resolves.toEqual(SAMPLE);
    });

    it("sends a POST with the correct path and full JSON body (incl. tags + enums)", async () => {
      const fetchMock = stubFetch(okJson(201, SAMPLE));
      await createPlant(INPUT);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants",
        expect.objectContaining({
          method: "POST",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(INPUT),
        }),
      );
    });

    it("sends location_id null for a homeless plant", async () => {
      const fetchMock = stubFetch(okJson(201, SAMPLE));
      await createPlant(HOMELESS_INPUT);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants",
        expect.objectContaining({
          method: "POST",
          body: JSON.stringify(HOMELESS_INPUT),
        }),
      );
    });

    it("throws ApiError on a non-2xx response (e.g. 422)", async () => {
      stubFetch(fail(422));
      await expect(createPlant(INPUT)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("updatePlant", () => {
    it("puts and parses the updated plant on 200", async () => {
      stubFetch(okJson(200, SAMPLE));
      await expect(updatePlant(1, INPUT)).resolves.toEqual(SAMPLE);
    });

    it("sends a PUT with the correct path and JSON body", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await updatePlant(3, INPUT);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/3",
        expect.objectContaining({
          method: "PUT",
          headers: {
            Accept: "application/json",
            "Content-Type": "application/json",
          },
          body: JSON.stringify(INPUT),
        }),
      );
    });

    it("throws ApiError on a non-2xx response", async () => {
      stubFetch(fail(404));
      await expect(updatePlant(99, INPUT)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("deletePlant", () => {
    it("resolves void on 204", async () => {
      stubFetch({ ok: true, status: 204 } as Response);
      await expect(deletePlant(1)).resolves.toBeUndefined();
    });

    it("sends a DELETE on the resource path", async () => {
      const fetchMock = stubFetch({ ok: true, status: 204 } as Response);
      await deletePlant(5);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/5",
        expect.objectContaining({ method: "DELETE" }),
      );
    });

    it("throws ApiError on a non-2xx response", async () => {
      stubFetch(fail(404));
      await expect(deletePlant(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("archivePlant", () => {
    it("posts to the archive sub-resource and parses the updated plant (US-2.4)", async () => {
      const archived: Plant = { ...SAMPLE, archived: true };
      const fetchMock = stubFetch(okJson(200, archived));
      await expect(archivePlant(1)).resolves.toEqual(archived);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/archive",
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
      await expect(archivePlant(99)).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("unarchivePlant", () => {
    it("posts to the unarchive sub-resource and parses the updated plant (US-2.4)", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));
      await expect(unarchivePlant(1)).resolves.toEqual(SAMPLE);
      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/plants/1/unarchive",
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
      await expect(unarchivePlant(99)).rejects.toBeInstanceOf(ApiError);
    });
  });
});
