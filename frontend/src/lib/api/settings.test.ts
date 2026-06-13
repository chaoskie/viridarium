import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import { getSettings, updateSettings, type AppSettings } from "./settings";

const SAMPLE: AppSettings = {
  seasonal_aware: true,
  winter_window: {
    start_month: 11,
    start_day: 1,
    end_month: 3,
    end_day: 1,
  },
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

describe("settings API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  describe("getSettings", () => {
    it("GETs the settings path with the JSON Accept header (F-1)", async () => {
      const fetchMock = stubFetch(okJson(200, SAMPLE));

      await expect(getSettings()).resolves.toEqual(SAMPLE);

      expect(fetchMock).toHaveBeenCalledWith(
        "/api/v1/settings",
        expect.objectContaining({ headers: { Accept: "application/json" } }),
      );
    });

    it("throws ApiError on a non-2xx response (F-3)", async () => {
      stubFetch(fail(500));
      await expect(getSettings()).rejects.toBeInstanceOf(ApiError);
    });
  });

  describe("updateSettings", () => {
    it("PUTs the settings path with the JSON body (F-2)", async () => {
      const input: AppSettings = {
        seasonal_aware: false,
        winter_window: {
          start_month: 5,
          start_day: 1,
          end_month: 9,
          end_day: 1,
        },
      };
      const fetchMock = stubFetch(okJson(200, input));

      await expect(updateSettings(input)).resolves.toEqual(input);

      expect(fetchMock).toHaveBeenCalledTimes(1);
      const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
      expect(path).toBe("/api/v1/settings");
      expect(init.method).toBe("PUT");
      expect(init.headers).toMatchObject({
        Accept: "application/json",
        "Content-Type": "application/json",
      });
      expect(init.body).toBe(JSON.stringify(input));
    });

    it("throws ApiError on a non-2xx response, incl. 422 (F-4)", async () => {
      stubFetch(fail(422));
      await expect(updateSettings(SAMPLE)).rejects.toBeInstanceOf(ApiError);
    });
  });
});
