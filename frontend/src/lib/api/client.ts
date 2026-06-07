/**
 * Minimal typed fetch wrapper for the Viridarium REST API.
 *
 * All requests target the versioned `/api/v1` base (SPEC E5: versioned path).
 * In dev, `/api` is proxied to the FastAPI backend (vite.config.ts).
 *
 * This is the walking-skeleton client: it exposes a single typed `getJson`
 * helper. Feature-specific endpoints will build on it as the API grows.
 */

export const API_BASE = "/api/v1";

/** Raised when the API responds with a non-2xx status. */
export class ApiError extends Error {
  readonly status: number;

  constructor(status: number, message: string) {
    super(message);
    this.name = "ApiError";
    this.status = status;
  }
}

/**
 * Perform a GET request and parse a JSON body of the expected shape.
 *
 * The caller supplies the expected type; the body is returned as that type.
 * No runtime validation is performed here - dedicated parsers will be added
 * per endpoint when the schemas exist.
 */
export async function getJson<T>(path: string): Promise<T> {
  const response = await fetch(`${API_BASE}${path}`, {
    headers: { Accept: "application/json" },
  });

  if (!response.ok) {
    throw new ApiError(
      response.status,
      `GET ${path} failed with ${String(response.status)}`,
    );
  }

  return (await response.json()) as T;
}
