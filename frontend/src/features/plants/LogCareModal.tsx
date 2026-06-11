import { useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { TextField } from "@/components/ui/TextField";
import {
  CARE_EVENT_TYPES,
  HEALTH_VALUES,
  todayIsoDate,
  type CareEvent,
  type CareEventInput,
  type CareEventType,
  type Health,
} from "@/lib/api/careEvents";
import { uploadPhoto } from "@/lib/api/photos";
import type { Plant } from "@/lib/api/plants";

import { useCareEvents } from "./useCareEvents";

interface LogCareModalProps {
  /** The plant this event is logged for. */
  readonly plant: Plant;
  /** Called with the created event on success (for inline feedback). */
  readonly onLogged: (event: CareEvent) => void;
  readonly onClose: () => void;
}

// Mirrors the server bound (proposal §domain: note max 10000, like plant notes).
const NOTE_MAX = 10000;

// Reuse the established control recipe (CareScheduleModal / PlantFormModal) so
// every control matches the theme tokens; NOT a new ui/ primitive (FE-010).
const CONTROL_CLASSES =
  "min-h-tap-min w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

const TYPE_LABELS: Record<CareEventType, string> = {
  water: "Water",
  feed: "Feed",
  repot: "Repot",
  observe: "Observe",
};

const HEALTH_LABELS: Record<Health, string> = {
  good: "Good",
  fair: "Fair",
  bad: "Bad",
};

const NO_HEALTH_VALUE = "";

/**
 * Log one care event for a plant (US-3.2, AC2): type select (the four event
 * kinds), date (defaults to today, max today - the future-date 422 is mirrored
 * client-side), optional note, optional photo file (uploaded via the existing
 * US-2.3 photos pipeline FIRST, then the event links the returned `photo_id`),
 * and a health select shown ONLY when type=observe (mirrors the server's
 * observe-only rule). Composes the shared `Modal`/`Button`/`TextField`
 * primitives plus the established control classes (FE-010/FE-011).
 */
export function LogCareModal({
  plant,
  onLogged,
  onClose,
}: LogCareModalProps): ReactNode {
  const today = todayIsoDate();
  const [type, setType] = useState<CareEventType>("water");
  const [date, setDate] = useState(today);
  const [note, setNote] = useState("");
  const [health, setHealth] = useState<string>(NO_HEALTH_VALUE);
  const [file, setFile] = useState<File | null>(null);

  const [dateError, setDateError] = useState<string | null>(null);
  const [photoError, setPhotoError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const { error: submitError, log } = useCareEvents(plant.id);

  const typeId = useId();
  const dateId = useId();
  const photoId = useId();
  const healthId = useId();

  // Over 20 lines: the submit is an ordered two-step pipeline (photo upload
  // BEFORE event create, AC2) with a distinct error surface per step.
  async function handleSubmit(): Promise<void> {
    setDateError(null);
    setPhotoError(null);
    if (date.trim().length === 0) {
      setDateError("Pick a date.");
      return;
    }
    if (date > today) {
      setDateError("Future dates are not allowed. Pick today or earlier.");
      return;
    }
    setSubmitting(true);

    let linkedPhotoId: number | null = null;
    if (file !== null) {
      try {
        linkedPhotoId = (await uploadPhoto(plant.id, file)).id;
      } catch {
        // The event is NOT created when its intended photo fails to upload.
        setPhotoError(
          "The photo could not be uploaded, so nothing was logged. Try a smaller JPEG/PNG/WebP, or remove the photo.",
        );
        setSubmitting(false);
        return;
      }
    }

    const trimmedNote = note.trim();
    const input: CareEventInput = {
      type,
      happened_on: date,
      ...(trimmedNote.length > 0 ? { note: trimmedNote } : {}),
      ...(linkedPhotoId !== null ? { photo_id: linkedPhotoId } : {}),
      ...(type === "observe" && health !== NO_HEALTH_VALUE
        ? { health: health as Health }
        : {}),
    };

    const created = await log(input);
    if (created === null) {
      // The hook trapped the failure into `submitError` (rendered below).
      setSubmitting(false);
      return;
    }
    onLogged(created);
    onClose();
  }

  return (
    <Modal title={`Log care - ${plant.name}`} onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        // all validation is custom (consistent field errors, incl. the
        // future-date mirror); native bubbles would preempt it for max
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor={typeId} className={LABEL_CLASSES}>
            Type
          </label>
          <select
            id={typeId}
            className={CONTROL_CLASSES}
            value={type}
            onChange={(event) => {
              const next = event.target.value as CareEventType;
              setType(next);
              if (next !== "observe") {
                // Health is observe-only; never carry it across a type switch.
                setHealth(NO_HEALTH_VALUE);
              }
            }}
          >
            {CARE_EVENT_TYPES.map((value) => (
              <option key={value} value={value}>
                {TYPE_LABELS[value]}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={dateId} className={LABEL_CLASSES}>
            Date
          </label>
          <input
            id={dateId}
            type="date"
            max={today}
            className={CONTROL_CLASSES}
            value={date}
            aria-invalid={dateError !== null || undefined}
            onChange={(event) => {
              setDate(event.target.value);
            }}
          />
          {dateError ? (
            <p className="font-body text-sm text-danger" role="alert">
              {dateError}
            </p>
          ) : null}
        </div>

        {type === "observe" ? (
          <div className="flex flex-col gap-1.5">
            <label htmlFor={healthId} className={LABEL_CLASSES}>
              Health
            </label>
            <select
              id={healthId}
              className={CONTROL_CLASSES}
              value={health}
              onChange={(event) => {
                setHealth(event.target.value);
              }}
            >
              <option value={NO_HEALTH_VALUE}>Not recorded</option>
              {HEALTH_VALUES.map((value) => (
                <option key={value} value={value}>
                  {HEALTH_LABELS[value]}
                </option>
              ))}
            </select>
          </div>
        ) : null}

        <TextField
          label="Note"
          value={note}
          onChange={setNote}
          multiline
          maxLength={NOTE_MAX}
          placeholder="Optional - anything worth remembering."
        />

        <div className="flex flex-col gap-1.5">
          <label htmlFor={photoId} className={LABEL_CLASSES}>
            Photo (optional)
          </label>
          <input
            id={photoId}
            type="file"
            accept="image/*"
            className={CONTROL_CLASSES}
            aria-invalid={photoError !== null || undefined}
            onChange={(event) => {
              setFile(event.target.files?.[0] ?? null);
            }}
          />
          {photoError ? (
            <p className="font-body text-sm text-danger" role="alert">
              {photoError}
            </p>
          ) : null}
        </div>

        {submitError !== null ? (
          <p className="font-body text-sm text-danger" role="alert">
            {submitError}
          </p>
        ) : null}

        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Logging..." : "Log event"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
