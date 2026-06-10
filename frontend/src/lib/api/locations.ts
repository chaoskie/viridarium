import { deleteResource, getJson, postJson, putJson } from "./client";

/**
 * A persisted location ("room") as returned by `GET /api/v1/locations`.
 *
 * Server response fields are snake_case (design §1: `created_at`/`updated_at`).
 * No runtime validation is performed; the shape mirrors `LocationResponse`.
 */
export interface Location {
  readonly id: number;
  readonly name: string;
  readonly notes: string | null;
  readonly created_at: string;
  readonly updated_at: string;
}

/** Request body for creating/updating a location (`LocationCreate`/`LocationUpdate`). */
export interface LocationInput {
  readonly name: string;
  readonly notes: string | null;
}

/** `GET /api/v1/locations` - all rooms, ordered by name. Throws `ApiError` on non-2xx. */
export function fetchLocations(): Promise<Location[]> {
  return getJson<Location[]>("/locations");
}

/** `GET /api/v1/locations/{id}` - one room. Throws `ApiError` on non-2xx. */
export function fetchLocation(id: number): Promise<Location> {
  return getJson<Location>(`/locations/${String(id)}`);
}

/** `POST /api/v1/locations` - create a room (201). Throws `ApiError` on non-2xx. */
export function createLocation(input: LocationInput): Promise<Location> {
  return postJson<Location>("/locations", input);
}

/** `PUT /api/v1/locations/{id}` - full-replace update (200). Throws `ApiError` on non-2xx. */
export function updateLocation(
  id: number,
  input: LocationInput,
): Promise<Location> {
  return putJson<Location>(`/locations/${String(id)}`, input);
}

/** `DELETE /api/v1/locations/{id}` - remove a room (204). Throws `ApiError` on non-2xx. */
export function deleteLocation(id: number): Promise<void> {
  return deleteResource(`/locations/${String(id)}`);
}
