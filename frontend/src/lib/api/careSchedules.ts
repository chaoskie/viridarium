import { deleteResource, getJson, putJson } from "./client";

/**
 * Care-type wire values (design §1, spec §3 vocabulary verbatim). Closed enum;
 * mirrors the backend `CareType` StrEnum.
 */
export type CareType = "water" | "feed";

/** All `CareType` values, for rendering the schedule sections. */
export const CARE_TYPES: readonly CareType[] = ["water", "feed"];

/**
 * Dormancy wire values (design §1 / CS2). `paused` skips the schedule in winter;
 * `winter_interval` switches to the (optional) winter cadence. Mirrors the
 * backend `Dormancy` StrEnum.
 */
export type Dormancy = "paused" | "winter_interval";

/**
 * A persisted care schedule as returned by the schedule endpoints
 * (`CareScheduleResponse`, design §1). Server fields are snake_case. The
 * response is keyed by `care_type` and OMITS the surrogate `id` (ARCH-007). No
 * runtime validation is performed; the shape mirrors `CareScheduleResponse`.
 */
export interface CareSchedule {
  readonly plant_id: number;
  readonly care_type: CareType;
  readonly interval_days: number;
  readonly winter_interval_days: number | null;
  readonly dormancy: Dormancy;
  readonly enabled: boolean;
  readonly created_at: string;
  readonly updated_at: string;
}

/**
 * Request body for the keyed PUT upsert (`CareScheduleUpsert`, design §1).
 * `care_type` is NOT part of the body - it travels in the path (design CS1). The
 * server defaults `dormancy` from the path care_type when it is omitted, so it
 * is optional here.
 */
export interface CareScheduleInput {
  readonly interval_days: number;
  readonly winter_interval_days: number | null;
  readonly dormancy?: Dormancy;
  readonly enabled: boolean;
}

/**
 * `GET /api/v1/plants/{id}/schedules` - the plant's schedules (0-2, water then
 * feed). Throws `ApiError` on non-2xx (incl. 404 for an unknown plant).
 */
export function fetchSchedules(plantId: number): Promise<CareSchedule[]> {
  return getJson<CareSchedule[]>(`/plants/${String(plantId)}/schedules`);
}

/**
 * `PUT /api/v1/plants/{id}/schedules/{care_type}` - idempotent create-or-replace
 * (design CS1). The `care_type` addresses the resource via the path; the body
 * carries no `care_type`. Returns the upserted `CareSchedule` (200). Throws
 * `ApiError` on non-2xx (incl. 404 plant, 422 validation/enum).
 */
export function upsertSchedule(
  plantId: number,
  careType: CareType,
  input: CareScheduleInput,
): Promise<CareSchedule> {
  return putJson<CareSchedule>(
    `/plants/${String(plantId)}/schedules/${careType}`,
    input,
  );
}

/**
 * `DELETE /api/v1/plants/{id}/schedules/{care_type}` - remove a schedule (204).
 * Throws `ApiError` on non-2xx (incl. 404 plant or no-schedule).
 */
export function deleteSchedule(
  plantId: number,
  careType: CareType,
): Promise<void> {
  return deleteResource(`/plants/${String(plantId)}/schedules/${careType}`);
}
