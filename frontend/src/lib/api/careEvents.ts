import { deleteResource, getJson, postJson } from "./client";

/**
 * Care-event wire values (proposal §domain, spec §3 vocabulary verbatim).
 * Closed enum; mirrors the backend `CareEventType` StrEnum. NOT the schedule
 * `CareType` - schedules stay water/feed; do not widen either enum.
 */
export type CareEventType = "water" | "feed" | "repot" | "observe";

/** All `CareEventType` values, for rendering the log form's type select. */
export const CARE_EVENT_TYPES: readonly CareEventType[] = [
  "water",
  "feed",
  "repot",
  "observe",
];

/**
 * Health wire values (proposal §domain). A journal input, only valid when
 * `type === "observe"` (else the server rejects with 422); never aggregated.
 */
export type Health = "good" | "fair" | "bad";

/** All `Health` values, for rendering the observe-only health select. */
export const HEALTH_VALUES: readonly Health[] = ["good", "fair", "bad"];

/**
 * A persisted care event as returned by the event endpoints
 * (`CareEventResponse`, proposal §API). Server fields are snake_case. Events
 * are append-only: there is no update route; `photo_id` is nulled server-side
 * when the linked photo is deleted. No runtime validation is performed; the
 * shape mirrors `CareEventResponse`.
 */
export interface CareEvent {
  readonly id: number;
  readonly plant_id: number;
  readonly type: CareEventType;
  readonly happened_on: string;
  readonly note: string | null;
  readonly photo_id: number | null;
  readonly health: Health | null;
  readonly created_at: string;
}

/**
 * Request body for `POST .../events` (proposal §API). `happened_on` defaults
 * to today server-side when omitted (future dates are 422); `photo_id` must
 * reference a photo of the same plant; `health` is observe-only. The body is
 * sent exactly as assembled - the quick-tap path sends `{type, happened_on}`
 * only.
 */
export interface CareEventInput {
  readonly type: CareEventType;
  readonly happened_on?: string;
  readonly note?: string;
  readonly photo_id?: number;
  readonly health?: Health;
}

/**
 * `GET /api/v1/plants/{id}/events` - the plant's events, newest first
 * (`happened_on` desc, then `created_at` desc). Throws `ApiError` on non-2xx
 * (incl. 404 for an unknown plant).
 */
export function fetchEvents(plantId: number): Promise<CareEvent[]> {
  return getJson<CareEvent[]>(`/plants/${String(plantId)}/events`);
}

/**
 * `POST /api/v1/plants/{id}/events` - append one care event. Returns the
 * created `CareEvent` (201). Throws `ApiError` on non-2xx (404 plant, 422
 * future date / health-on-non-observe / cross-plant photo).
 */
export function createEvent(
  plantId: number,
  input: CareEventInput,
): Promise<CareEvent> {
  return postJson<CareEvent>(`/plants/${String(plantId)}/events`, input);
}

/**
 * `DELETE /api/v1/plants/{id}/events/{eventId}` - remove one event (204;
 * mistakes only - events are otherwise append-only). Throws `ApiError` on
 * non-2xx (incl. 404 for an unknown plant, missing or cross-plant event).
 */
export function deleteEvent(plantId: number, eventId: number): Promise<void> {
  return deleteResource(`/plants/${String(plantId)}/events/${String(eventId)}`);
}

/**
 * Today's local calendar date as `YYYY-MM-DD` - the `happened_on` value for
 * the one-tap quick actions and the log form's default/max (local time, not
 * UTC, so a late-evening tap never logs tomorrow).
 */
export function todayIsoDate(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}
