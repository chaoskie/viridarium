import { getJson } from "./client";

/** Shape of `GET /api/v1/health` (E1 walking skeleton). */
export interface HealthStatus {
  status: string;
}

/** Fetch backend health. Throws `ApiError` on a non-2xx response. */
export function fetchHealth(): Promise<HealthStatus> {
  return getJson<HealthStatus>("/health");
}
