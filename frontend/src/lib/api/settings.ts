import { getJson, putJson } from "./client";

/**
 * The winter window as month/day endpoints (both inclusive, year-agnostic, may
 * wrap the new year). Mirrors the backend `winter_window` block of
 * `SettingsResponse`; server fields are snake_case.
 */
export interface WinterWindow {
  readonly start_month: number;
  readonly start_day: number;
  readonly end_month: number;
  readonly end_day: number;
}

/**
 * The persisted app settings as returned by the settings endpoints
 * (`SettingsResponse`, design §7). The shape is exactly
 * `{seasonal_aware, winter_window:{...}}`; the surrogate `id` and `updated_at`
 * never cross the boundary (ARCH-007). No runtime validation is performed; the
 * shape mirrors the server response. PUT uses the same shape as GET.
 */
export interface AppSettings {
  readonly seasonal_aware: boolean;
  readonly winter_window: WinterWindow;
}

/**
 * `GET /api/v1/settings` - the persisted settings, or the spec default on a
 * fresh install (AC1). Throws `ApiError` on non-2xx.
 */
export function getSettings(): Promise<AppSettings> {
  return getJson<AppSettings>("/settings");
}

/**
 * `PUT /api/v1/settings` - persist the settings; the server echoes the stored
 * value (200). Throws `ApiError` on non-2xx (incl. 422 on an invalid
 * month/day, surfaced inline by the page).
 */
export function updateSettings(input: AppSettings): Promise<AppSettings> {
  return putJson<AppSettings>("/settings", input);
}
