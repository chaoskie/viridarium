import type { CareEventType, Health } from "./careEvents";
import { getJson } from "./client";

/**
 * The nested photo reference of a timeline entry (`TimelinePhotoSchema`, the
 * §7 contract). Exactly `{id, url}` - never `stored_filename` (the on-disk
 * security boundary, ARCH-007). `url` is the server-computed bytes endpoint
 * (`/api/v1/plants/{plant_id}/photos/{id}`); the client renders it directly.
 */
export interface TimelinePhotoRef {
  readonly id: number;
  readonly url: string;
}

/**
 * A care-event timeline entry (`kind:"event"`, the §7 contract). `date` is the
 * event's `happened_on`; `health` is non-null only on observe events; `photo`
 * is the inline linked photo or null.
 */
export interface TimelineEvent {
  readonly kind: "event";
  readonly date: string;
  readonly event_type: CareEventType;
  readonly note: string | null;
  readonly health: Health | null;
  readonly photo: TimelinePhotoRef | null;
}

/**
 * A standalone (unlinked) photo timeline entry (`kind:"photo"`, the §7
 * contract). `date` is the photo's `created_at` date; `photo` is always present.
 */
export interface TimelinePhoto {
  readonly kind: "photo";
  readonly date: string;
  readonly photo: TimelinePhotoRef;
}

/**
 * One merged timeline entry: the discriminated union of the two arms, narrowed
 * on `kind` (the server merges events + photos server-side; the client renders
 * the feed verbatim, never re-sorting - AC1). No runtime validation is
 * performed; the shape mirrors the backend `TimelineEntryResponse` union.
 */
export type TimelineEntry = TimelineEvent | TimelinePhoto;

/**
 * `GET /api/v1/plants/{id}/timeline` - the plant's full history, newest-first:
 * its care events (each with any inline photo) merged with its standalone
 * photos. Throws `ApiError` on non-2xx (incl. 404 for an unknown plant).
 */
export function getTimeline(plantId: number): Promise<TimelineEntry[]> {
  return getJson<TimelineEntry[]>(`/plants/${String(plantId)}/timeline`);
}
