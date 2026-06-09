import {
  API_BASE,
  deleteResource,
  getJson,
  postFormData,
  postJson,
} from "./client";

/**
 * A persisted photo as returned by the photo endpoints (`PhotoResponse`,
 * design §1). Server fields are snake_case. `url` is the server-computed path
 * to the raw bytes (`/api/v1/plants/{plant_id}/photos/{id}`); `stored_filename`
 * never crosses the response boundary (security boundary, ARCH-007). No runtime
 * validation is performed; the shape mirrors `PhotoResponse`.
 */
export interface Photo {
  readonly id: number;
  readonly plant_id: number;
  readonly content_type: string;
  readonly size_bytes: number;
  readonly is_cover: boolean;
  readonly created_at: string;
  readonly url: string;
}

/**
 * `GET /api/v1/plants/{id}/photos` - the plant's photos, newest-first (P5).
 * Throws `ApiError` on non-2xx (incl. 404 for an unknown plant).
 */
export function fetchPhotos(plantId: number): Promise<Photo[]> {
  return getJson<Photo[]>(`/plants/${String(plantId)}/photos`);
}

/**
 * `POST /api/v1/plants/{id}/photos` - upload one image as `multipart/form-data`
 * with the field name `file` (design §1). Returns the created `Photo` (201).
 * Throws `ApiError` on non-2xx (415 bad type/magic, 413 oversize, 404 plant).
 */
export function uploadPhoto(plantId: number, file: File): Promise<Photo> {
  const form = new FormData();
  form.append("file", file);
  return postFormData<Photo>(`/plants/${String(plantId)}/photos`, form);
}

/**
 * `POST /api/v1/plants/{id}/photos/{photoId}/cover` - make this photo the cover
 * (empty body; the server clears any other cover in-tx). Returns the updated
 * `Photo` (200). Throws `ApiError` on non-2xx (incl. 404).
 */
export function setCoverPhoto(
  plantId: number,
  photoId: number,
): Promise<Photo> {
  return postJson<Photo>(
    `/plants/${String(plantId)}/photos/${String(photoId)}/cover`,
    {},
  );
}

/**
 * `DELETE /api/v1/plants/{id}/photos/{photoId}` - remove a photo (204; the
 * server unlinks the file and promotes the newest survivor if the cover was
 * removed). Throws `ApiError` on non-2xx (incl. 404).
 */
export function deletePhoto(plantId: number, photoId: number): Promise<void> {
  return deleteResource(`/plants/${String(plantId)}/photos/${String(photoId)}`);
}

/**
 * The raw-bytes URL for an `<img src>` (the same value the server computes as
 * `PhotoResponse.url`). Built locally so a card can render a cover thumbnail
 * without re-deriving the path. Mirrors `GET .../photos/{id}`.
 */
export function photoUrl(plantId: number, photoId: number): string {
  return `${API_BASE}/plants/${String(plantId)}/photos/${String(photoId)}`;
}
