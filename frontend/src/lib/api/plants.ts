import { deleteResource, getJson, postJson, putJson } from "./client";

/**
 * Pot material wire values (design §1 / D3). String-literal union matching the
 * backend `PotMaterial` StrEnum members exactly.
 */
export type PotMaterial =
  | "terracotta"
  | "plastic"
  | "ceramic"
  | "self-watering"
  | "other";

/**
 * Light-level wire values (design §1 / D3). String-literal union matching the
 * backend `LightLevel` StrEnum members exactly.
 */
export type LightLevel = "dark" | "indirect" | "bright-indirect" | "full-sun";

/** All `PotMaterial` values, for rendering the select options. */
export const POT_MATERIALS: readonly PotMaterial[] = [
  "terracotta",
  "plastic",
  "ceramic",
  "self-watering",
  "other",
];

/** All `LightLevel` values, for rendering the select options. */
export const LIGHT_LEVELS: readonly LightLevel[] = [
  "dark",
  "indirect",
  "bright-indirect",
  "full-sun",
];

/**
 * One enabled schedule's due state as returned inside `PlantResponse.schedules`
 * (the additive US-3.3 field; `ScheduleDueResponse` on the wire). `care_type` is
 * the closed schedule vocabulary `water`/`feed` - NOT the four-member
 * `CareEventType`. `next_due` is null only when the schedule is paused/dormant
 * inside the window; `overdue_days` is null iff `next_due` is null (the
 * both-null invariant), else `>= 0`.
 */
export interface ScheduleDue {
  readonly care_type: "water" | "feed";
  readonly next_due: string | null;
  readonly overdue_days: number | null;
}

/**
 * A persisted plant as returned by `GET /api/v1/plants` (`PlantResponse`).
 *
 * Server response fields are snake_case (design §1). `location_id` is null when
 * the plant is homeless (D-009). No runtime validation is performed; the shape
 * mirrors `PlantResponse`.
 */
export interface Plant {
  readonly id: number;
  readonly name: string;
  readonly species: string | null;
  readonly location_id: number | null;
  readonly acquired_on: string | null;
  readonly pot_size_cm: number | null;
  readonly pot_material: PotMaterial | null;
  readonly light_level: LightLevel | null;
  readonly notes: string | null;
  readonly tags: readonly string[];
  readonly archived: boolean;
  readonly cover_photo_id: number | null;
  /**
   * One entry per enabled schedule of the plant, carrying its computed due
   * state (US-3.3, additive; already on the wire). Archived plants and plants
   * with no enabled schedule carry `[]`.
   */
  readonly schedules: readonly ScheduleDue[];
  readonly created_at: string;
  readonly updated_at: string;
}

/** Request body for creating/updating a plant (`PlantCreate`/`PlantUpdate`). */
export interface PlantInput {
  readonly name: string;
  readonly species: string | null;
  readonly location_id: number | null;
  readonly acquired_on: string | null;
  readonly pot_size_cm: number | null;
  readonly pot_material: PotMaterial | null;
  readonly light_level: LightLevel | null;
  readonly notes: string | null;
  readonly tags: readonly string[];
  readonly archived: boolean;
}

/**
 * Optional search/filter params for the list endpoint (design §1 / D4).
 * All optional and AND-combined server-side. `homeless=true` returns only
 * null-location plants. Unset / empty fields are omitted from the query string.
 */
export interface PlantFilter {
  readonly q?: string;
  readonly location_id?: number | null;
  readonly tag?: string;
  readonly species?: string;
  readonly homeless?: boolean;
  readonly archived?: boolean;
  readonly include_archived?: boolean;
}

/**
 * Render a `PlantFilter` to a `?...` query string. Only set, non-empty fields
 * are appended (D4 - all params optional); an empty/undefined filter yields the
 * bare collection path. `homeless` is rendered only when true.
 */
function buildQuery(filter: PlantFilter | undefined): string {
  if (filter === undefined) {
    return "";
  }
  const params = new URLSearchParams();
  if (filter.q !== undefined && filter.q.length > 0) {
    params.set("q", filter.q);
  }
  if (filter.location_id !== undefined && filter.location_id !== null) {
    params.set("location_id", String(filter.location_id));
  }
  if (filter.tag !== undefined && filter.tag.length > 0) {
    params.set("tag", filter.tag);
  }
  if (filter.species !== undefined && filter.species.length > 0) {
    params.set("species", filter.species);
  }
  if (filter.homeless === true) {
    params.set("homeless", "true");
  }
  // `archived` is a tri-state scope (A2): unset -> active (server default),
  // true -> archived only, false -> active only. Render whenever set.
  if (filter.archived !== undefined) {
    params.set("archived", String(filter.archived));
  }
  // `include_archived` overrides the scope to "all"; render only when true
  // (mirrors `homeless`).
  if (filter.include_archived === true) {
    params.set("include_archived", "true");
  }
  const query = params.toString();
  return query.length > 0 ? `?${query}` : "";
}

/**
 * `GET /api/v1/plants` - all plants ordered by name, narrowed by the optional
 * filter. Throws `ApiError` on non-2xx.
 */
export function fetchPlants(filter?: PlantFilter): Promise<Plant[]> {
  return getJson<Plant[]>(`/plants${buildQuery(filter)}`);
}

/** `GET /api/v1/plants/{id}` - one plant. Throws `ApiError` on non-2xx. */
export function fetchPlant(id: number): Promise<Plant> {
  return getJson<Plant>(`/plants/${String(id)}`);
}

/** `POST /api/v1/plants` - create a plant (201). Throws `ApiError` on non-2xx. */
export function createPlant(input: PlantInput): Promise<Plant> {
  return postJson<Plant>("/plants", input);
}

/** `PUT /api/v1/plants/{id}` - full-replace update (200). Throws `ApiError` on non-2xx. */
export function updatePlant(id: number, input: PlantInput): Promise<Plant> {
  return putJson<Plant>(`/plants/${String(id)}`, input);
}

/** `DELETE /api/v1/plants/{id}` - remove a plant (204). Throws `ApiError` on non-2xx. */
export function deletePlant(id: number): Promise<void> {
  return deleteResource(`/plants/${String(id)}`);
}

/**
 * `POST /api/v1/plants/{id}/archive` - idempotent state-set action (US-2.4 / A1).
 * Empty body; returns the updated `PlantResponse` (200). Throws `ApiError` on
 * non-2xx (incl. 404 for an unknown id).
 */
export function archivePlant(id: number): Promise<Plant> {
  return postJson<Plant>(`/plants/${String(id)}/archive`, {});
}

/**
 * `POST /api/v1/plants/{id}/unarchive` - idempotent state-set action (US-2.4 / A1).
 * Empty body; returns the updated `PlantResponse` (200). Throws `ApiError` on
 * non-2xx (incl. 404 for an unknown id).
 */
export function unarchivePlant(id: number): Promise<Plant> {
  return postJson<Plant>(`/plants/${String(id)}/unarchive`, {});
}
