import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import { fetchHealth } from "./health";

function mockFetchOnce(response: Partial<Response>): void {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(response));
}

describe("fetchHealth", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("returns the parsed health status on a 200 (happy path)", async () => {
    mockFetchOnce({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: "ok" }),
    });

    await expect(fetchHealth()).resolves.toEqual({ status: "ok" });
  });

  it("calls the versioned health endpoint", async () => {
    const fetchMock = vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve({ status: "ok" }),
    });
    vi.stubGlobal("fetch", fetchMock);

    await fetchHealth();

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/health",
      expect.objectContaining({
        headers: { Accept: "application/json" },
      }),
    );
  });

  it("throws ApiError on a non-2xx response (sad path)", async () => {
    mockFetchOnce({
      ok: false,
      status: 503,
      json: () => Promise.resolve({}),
    });

    await expect(fetchHealth()).rejects.toBeInstanceOf(ApiError);
  });
});
