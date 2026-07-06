import type { ReactNode } from "react";

import type { Photo } from "@/lib/api/photos";
import type { Plant } from "@/lib/api/plants";

import { usePhotos } from "./usePhotos";

/** Thumbnail-strip cap; more photos collapse into a "+N" affordance (§5). */
export const THUMB_CAP = 8;

interface PlantGalleryProps {
  readonly plant: Plant;
  /** Opens the existing `PhotoGalleryModal` (view/manage). */
  readonly onOpen: () => void;
}

const THUMB_BUTTON_CLASSES =
  "min-h-tap-min rounded-control focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

/**
 * The detail page's inline gallery (US-4.3, AC3): the cover photo prominent
 * (falling back to the newest photo when no cover is set) plus a capped
 * thumbnail strip with a "+N" overflow; every tap opens the existing
 * `PhotoGalleryModal`. A plant with no photos shows an empty state and never
 * a broken image. Photos come from the existing `usePhotos` hook.
 */
export function PlantGallery({ plant, onOpen }: PlantGalleryProps): ReactNode {
  const { photos, loading } = usePhotos(plant.id);

  const prominent: Photo | null =
    photos.find((photo) => photo.id === plant.cover_photo_id) ??
    photos[0] ??
    null;
  const remaining = photos.filter((photo) => photo.id !== prominent?.id);
  const thumbs = remaining.slice(0, THUMB_CAP);
  const hidden = remaining.length - thumbs.length;

  return (
    <section
      aria-label="Photos"
      className="flex flex-col gap-3 rounded-card border-card border-border bg-surface-raised p-5 shadow-card"
    >
      <h2 className="font-display text-xl font-semibold text-ink">Photos</h2>
      {prominent === null ? (
        loading ? null : (
          <p className="font-body text-base text-ink-muted">
            No photos yet. Open the gallery to add one.
          </p>
        )
      ) : (
        <div className="flex flex-col gap-3">
          <button
            type="button"
            aria-label={`Open photos of ${plant.name}`}
            className={THUMB_BUTTON_CLASSES}
            onClick={onOpen}
          >
            <img
              src={prominent.url}
              alt={`${plant.name} cover photo`}
              className="max-h-80 w-full rounded-control border-control border-border object-cover"
            />
          </button>
          {thumbs.length > 0 || hidden > 0 ? (
            <ul className="flex flex-wrap gap-2">
              {thumbs.map((photo, index) => (
                <li key={photo.id}>
                  <button
                    type="button"
                    aria-label={`Open photo ${String(index + 1)} of ${plant.name}`}
                    className={THUMB_BUTTON_CLASSES}
                    onClick={onOpen}
                  >
                    <img
                      src={photo.url}
                      alt={`${plant.name} photo`}
                      loading="lazy"
                      className="h-16 w-16 rounded-control border-control border-border object-cover"
                    />
                  </button>
                </li>
              ))}
              {hidden > 0 ? (
                <li>
                  <button
                    type="button"
                    aria-label={`View all ${String(photos.length)} photos of ${plant.name}`}
                    className="grid h-16 w-16 min-h-tap-min place-items-center rounded-control border-control border-border bg-surface-sunken font-label text-sm font-semibold text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
                    onClick={onOpen}
                  >
                    +{String(hidden)}
                  </button>
                </li>
              ) : null}
            </ul>
          ) : null}
        </div>
      )}
    </section>
  );
}
