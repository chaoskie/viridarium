import { useId, useRef, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type { Plant } from "@/lib/api/plants";
import { photoUrl } from "@/lib/api/photos";

import { usePhotos } from "./usePhotos";

interface PhotoGalleryModalProps {
  /** The plant whose gallery this modal manages. */
  readonly plant: Plant;
  readonly onClose: () => void;
}

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

// Reuse the existing pill recipe (PlantsPage tags/archived chip) so the cover
// badge matches every theme token (FE-002/FE-010: a combination, not a new one).
const PILL_CLASSES =
  "rounded-pill border-control border-border bg-surface-sunken px-2 py-0.5 font-label text-xs uppercase tracking-widest text-ink-muted";

// Token-styled thumbnail; full image sized down via CSS (no server thumbnails).
const THUMB_CLASSES =
  "h-24 w-24 rounded-control border-control border-border object-cover";

// The accepted upload types mirror the server allowlist (jpeg/png/webp, P2).
const ACCEPT = "image/jpeg,image/png,image/webp";

/**
 * Per-plant photo gallery (US-2.3, AC10). Composes the shared `Modal` + `Button`
 * primitives (FE-010: no new primitive). Shows a newest-first thumbnail grid;
 * the cover thumbnail carries a "Cover" pill; each thumbnail offers "Set cover"
 * (hidden on the current cover) and "Delete". A labelled file input + an
 * "Upload" button drive `usePhotos.upload`. Loading / empty / error states are
 * surfaced inline (FE-011: every control has an accessible name, ≥44px taps).
 */
export function PhotoGalleryModal({
  plant,
  onClose,
}: PhotoGalleryModalProps): ReactNode {
  const { photos, loading, error, upload, setCover, remove } = usePhotos(
    plant.id,
  );
  const [selected, setSelected] = useState<File | null>(null);
  const [busy, setBusy] = useState(false);
  const fileInputRef = useRef<HTMLInputElement>(null);
  const fileInputId = useId();

  async function handleUpload(): Promise<void> {
    if (selected === null) {
      return;
    }
    setBusy(true);
    await upload(selected);
    setBusy(false);
    // Clear the picker so the same file can be re-selected and the label resets.
    setSelected(null);
    if (fileInputRef.current !== null) {
      fileInputRef.current.value = "";
    }
  }

  return (
    <Modal title={`Photos - ${plant.name}`} onClose={onClose}>
      <div className="flex flex-col gap-4">
        <div className="flex flex-col gap-1.5">
          <label htmlFor={fileInputId} className={LABEL_CLASSES}>
            Add a photo (JPEG, PNG, or WebP)
          </label>
          <div className="flex flex-wrap items-center gap-2">
            <input
              ref={fileInputRef}
              id={fileInputId}
              type="file"
              accept={ACCEPT}
              className="min-h-tap-min font-body text-sm text-ink file:mr-3 file:min-h-tap-min file:rounded-control file:border-control file:border-border file:bg-surface file:px-3 file:font-label file:text-sm file:font-semibold file:uppercase file:tracking-widest file:text-ink"
              onChange={(event) => {
                const file = event.target.files?.[0] ?? null;
                setSelected(file);
              }}
            />
            <Button
              variant="primary"
              aria-label={`Upload a photo for ${plant.name}`}
              disabled={selected === null || busy}
              onClick={() => {
                void handleUpload();
              }}
            >
              {busy ? "Uploading..." : "Upload"}
            </Button>
          </div>
        </div>

        {error !== null ? (
          <p className="font-body text-sm text-danger" role="alert">
            {error}
          </p>
        ) : null}

        {loading ? (
          <p
            className="font-label text-sm uppercase tracking-wide text-ink-muted"
            aria-live="polite"
          >
            Loading photos...
          </p>
        ) : null}

        {!loading && error === null && photos.length === 0 ? (
          <p className="font-body text-base text-ink-muted">
            No photos yet. Upload one above.
          </p>
        ) : null}

        {!loading && photos.length > 0 ? (
          <ul className="grid grid-cols-2 gap-3 sm:grid-cols-3">
            {photos.map((photo) => (
              <li
                key={photo.id}
                className="flex flex-col items-center gap-2 rounded-card border-card border-border bg-surface p-2 shadow-card"
              >
                <img
                  src={photoUrl(plant.id, photo.id)}
                  alt={`${plant.name} photo`}
                  loading="lazy"
                  className={THUMB_CLASSES}
                />
                {photo.is_cover ? (
                  <span className={PILL_CLASSES}>Cover</span>
                ) : null}
                <div className="flex w-full flex-col gap-1.5">
                  {!photo.is_cover ? (
                    <Button
                      variant="ghost"
                      aria-label={`Set this photo as the cover for ${plant.name}`}
                      onClick={() => {
                        void setCover(photo.id);
                      }}
                    >
                      Set cover
                    </Button>
                  ) : null}
                  <Button
                    variant="danger"
                    aria-label={`Delete this photo of ${plant.name}`}
                    onClick={() => {
                      void remove(photo.id);
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            ))}
          </ul>
        ) : null}

        <div className="flex justify-end">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
