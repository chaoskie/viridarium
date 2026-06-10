import { useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import {
  CARE_TYPES,
  type CareSchedule,
  type CareScheduleInput,
  type CareType,
  type Dormancy,
} from "@/lib/api/careSchedules";
import type { Plant } from "@/lib/api/plants";

import { useCareSchedules } from "./useCareSchedules";

interface CareScheduleModalProps {
  /** The plant whose schedules this modal manages. */
  readonly plant: Plant;
  readonly onClose: () => void;
}

// Reuse the established control recipe (PlantsPage `<select>`/inputs) so every
// control matches the theme tokens; NOT a new ui/ primitive (FE-010).
const CONTROL_CLASSES =
  "min-h-tap-min w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

const DORMANCY_VALUES: readonly Dormancy[] = ["paused", "winter_interval"];

const DORMANCY_LABELS: Record<Dormancy, string> = {
  paused: "Pause in winter",
  winter_interval: "Use winter interval",
};

const CARE_TYPE_LABELS: Record<CareType, string> = {
  water: "Water",
  feed: "Feed",
};

/** Care-type default dormancy at the HTTP boundary (design CS2). */
const DEFAULT_DORMANCY: Record<CareType, Dormancy> = {
  water: "winter_interval",
  feed: "paused",
};

/** Parse a number-input string to a positive integer, or null when empty/bad. */
function parsePositiveInt(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed.length === 0) {
    return null;
  }
  const value = Number(trimmed);
  if (!Number.isInteger(value) || value < 1) {
    return null;
  }
  return value;
}

interface ScheduleSectionProps {
  readonly plantName: string;
  readonly careType: CareType;
  readonly existing: CareSchedule | undefined;
  readonly onSave: (careType: CareType, input: CareScheduleInput) => void;
  readonly onRemove: (careType: CareType) => void;
}

/**
 * One care-type section (water or feed): enabled checkbox, required interval,
 * optional winter interval, dormancy `<select>`. Pre-filled from the fetched
 * schedule when one exists. Renders the dismissible no-winter-interval hint
 * (PO Q2): non-blocking, never prevents saving.
 */
function ScheduleSection({
  plantName,
  careType,
  existing,
  onSave,
  onRemove,
}: ScheduleSectionProps): ReactNode {
  const [enabled, setEnabled] = useState<boolean>(existing?.enabled ?? true);
  const [interval, setInterval] = useState<string>(
    existing !== undefined ? String(existing.interval_days) : "",
  );
  const [winterInterval, setWinterInterval] = useState<string>(
    existing?.winter_interval_days != null
      ? String(existing.winter_interval_days)
      : "",
  );
  const [dormancy, setDormancy] = useState<Dormancy>(
    existing?.dormancy ?? DEFAULT_DORMANCY[careType],
  );
  const [hintDismissed, setHintDismissed] = useState<boolean>(false);

  const enabledId = useId();
  const intervalId = useId();
  const winterId = useId();
  const dormancyId = useId();

  const label = CARE_TYPE_LABELS[careType];
  const parsedInterval = parsePositiveInt(interval);
  const parsedWinter = parsePositiveInt(winterInterval);

  // The hint nudges (non-blocking): winter_interval dormancy with no winter
  // interval set keeps the normal cadence year-round (CS3, spec "if set").
  const showHint =
    !hintDismissed &&
    dormancy === "winter_interval" &&
    winterInterval.trim().length === 0;

  function handleSave(): void {
    if (parsedInterval === null) {
      return;
    }
    onSave(careType, {
      interval_days: parsedInterval,
      winter_interval_days: parsedWinter,
      dormancy,
      enabled,
    });
  }

  return (
    <section
      role="group"
      aria-label={`${label} schedule`}
      className="flex flex-col gap-3 rounded-card border-card border-border bg-surface p-4"
    >
      <h3 className="font-display text-xl font-semibold text-ink">{label}</h3>

      <label htmlFor={enabledId} className="flex items-center gap-2">
        <input
          id={enabledId}
          type="checkbox"
          checked={enabled}
          className="min-h-tap-min min-w-tap-min accent-accent"
          onChange={(event) => {
            setEnabled(event.target.checked);
          }}
        />
        <span className="font-body text-base text-ink">Enabled</span>
      </label>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={intervalId} className={LABEL_CLASSES}>
          Interval (days)
          <span className="text-danger"> *</span>
        </label>
        <input
          id={intervalId}
          type="number"
          min={1}
          max={3650}
          inputMode="numeric"
          className={CONTROL_CLASSES}
          value={interval}
          placeholder="e.g. 7"
          onChange={(event) => {
            setInterval(event.target.value);
          }}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={winterId} className={LABEL_CLASSES}>
          Winter interval (days, optional)
        </label>
        <input
          id={winterId}
          type="number"
          min={1}
          max={3650}
          inputMode="numeric"
          className={CONTROL_CLASSES}
          value={winterInterval}
          placeholder="Leave empty for the same cadence"
          onChange={(event) => {
            setWinterInterval(event.target.value);
          }}
        />
      </div>

      <div className="flex flex-col gap-1.5">
        <label htmlFor={dormancyId} className={LABEL_CLASSES}>
          Winter behaviour
        </label>
        <select
          id={dormancyId}
          className={CONTROL_CLASSES}
          value={dormancy}
          onChange={(event) => {
            setDormancy(event.target.value as Dormancy);
          }}
        >
          {DORMANCY_VALUES.map((value) => (
            <option key={value} value={value}>
              {DORMANCY_LABELS[value]}
            </option>
          ))}
        </select>
      </div>

      {showHint ? (
        <div
          role="note"
          className="flex items-start justify-between gap-2 rounded-control border-control border-border bg-surface-sunken p-3"
        >
          <p className="font-body text-sm text-ink-muted">
            No winter interval set - this schedule keeps the normal cadence
            year-round. You can set one if you slow{" "}
            {careType === "water" ? "watering" : "feeding"} in winter.
          </p>
          <button
            type="button"
            aria-label={`Dismiss the winter interval hint for ${label.toLowerCase()}`}
            className="grid min-h-tap-min min-w-tap-min shrink-0 place-items-center rounded-control border-control border-transparent text-lg text-ink-muted hover:bg-surface hover:text-ink"
            onClick={() => {
              setHintDismissed(true);
            }}
          >
            ✕
          </button>
        </div>
      ) : null}

      <div className="flex flex-wrap justify-end gap-2">
        {existing !== undefined ? (
          <Button
            variant="danger"
            aria-label={`Remove the ${label.toLowerCase()} schedule for ${plantName}`}
            onClick={() => {
              onRemove(careType);
            }}
          >
            Remove
          </Button>
        ) : null}
        <Button
          variant="primary"
          aria-label={`Save the ${label.toLowerCase()} schedule for ${plantName}`}
          disabled={parsedInterval === null}
          onClick={handleSave}
        >
          Save
        </Button>
      </div>
    </section>
  );
}

/**
 * Per-plant care-schedule config (US-3.1, AC9). Composes the shared `Modal` +
 * `Button` primitives plus the established control classes (FE-010: no new
 * primitive). Renders a water and a feed section, each pre-filled from the
 * fetched schedule when one exists. "Save" upserts via the keyed PUT; "Remove"
 * deletes. The no-winter-interval hint is a small, dismissible, non-blocking
 * note (PO Q2). Loading / error states are surfaced inline (FE-011: every
 * control has an accessible name, ≥44px taps).
 */
export function CareScheduleModal({
  plant,
  onClose,
}: CareScheduleModalProps): ReactNode {
  const { schedules, loading, error, upsert, remove } = useCareSchedules(
    plant.id,
  );

  function scheduleFor(careType: CareType): CareSchedule | undefined {
    return schedules.find((schedule) => schedule.care_type === careType);
  }

  return (
    <Modal title={`Schedules - ${plant.name}`} onClose={onClose}>
      <div className="flex flex-col gap-4">
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
            Loading schedules...
          </p>
        ) : (
          CARE_TYPES.map((careType) => (
            <ScheduleSection
              // Re-key on the loaded schedule's timestamp so the section resets
              // its pre-filled state when the server data changes after a save.
              key={`${careType}-${scheduleFor(careType)?.updated_at ?? "new"}`}
              plantName={plant.name}
              careType={careType}
              existing={scheduleFor(careType)}
              onSave={(type, input) => {
                void upsert(type, input);
              }}
              onRemove={(type) => {
                void remove(type);
              }}
            />
          ))
        )}

        <div className="flex justify-end">
          <Button variant="ghost" onClick={onClose}>
            Close
          </Button>
        </div>
      </div>
    </Modal>
  );
}
