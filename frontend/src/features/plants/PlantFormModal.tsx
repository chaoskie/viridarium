import { useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { TextField } from "@/components/ui/TextField";
import { ApiError } from "@/lib/api/client";
import type { Location } from "@/lib/api/locations";
import {
  LIGHT_LEVELS,
  POT_MATERIALS,
  type LightLevel,
  type Plant,
  type PlantInput,
  type PotMaterial,
} from "@/lib/api/plants";

interface PlantFormModalProps {
  /** Existing plant when editing; absent when creating. */
  readonly plant?: Plant | undefined;
  /** Rooms for the location picker (shared `lib/api`, FE-008-allowed). */
  readonly locations: readonly Location[];
  readonly onSubmit: (input: PlantInput) => Promise<void>;
  readonly onClose: () => void;
}

// Mirrors the server bounds (design §1).
const NAME_MAX = 120;
const SPECIES_MAX = 200;
const NOTES_MAX = 10000;
const POT_SIZE_MIN = 1;
const POT_SIZE_MAX = 500;

// Reuse TextField's control classes verbatim so the selects match every theme
// token (FE-002/FE-010: a new combination of existing primitives, not a new one).
const SELECT_CLASSES =
  "min-h-tap-min w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

/** A labeled native `<select>` styled with the existing control tokens (FE-011: labelled). */
function FieldSelect({
  label,
  value,
  options,
  onChange,
}: {
  readonly label: string;
  readonly value: string;
  readonly options: readonly {
    readonly value: string;
    readonly label: string;
  }[];
  readonly onChange: (value: string) => void;
}): ReactNode {
  const id = useId();
  return (
    <div className="flex flex-col gap-1.5">
      <label htmlFor={id} className={LABEL_CLASSES}>
        {label}
      </label>
      <select
        id={id}
        className={SELECT_CLASSES}
        value={value}
        onChange={(event) => {
          onChange(event.target.value);
        }}
      >
        {options.map((option) => (
          <option key={option.value} value={option.value}>
            {option.label}
          </option>
        ))}
      </select>
    </div>
  );
}

const HOMELESS_VALUE = "";

/** Parse a comma/whitespace tag string into a deduped, trimmed, non-empty list. */
function parseTags(raw: string): string[] {
  const seen = new Set<string>();
  for (const part of raw.split(",")) {
    const trimmed = part.trim();
    if (trimmed.length > 0) {
      seen.add(trimmed);
    }
  }
  return [...seen];
}

/** Convert an integer field string to a number or null (empty/non-integer -> null). */
function parseOptionalInt(raw: string): number | null {
  const trimmed = raw.trim();
  if (trimmed.length === 0) {
    return null;
  }
  const parsed = Number(trimmed);
  return Number.isInteger(parsed) ? parsed : null;
}

/** Convert an optional text field to a trimmed value or null. */
function orNull(raw: string): string | null {
  const trimmed = raw.trim();
  return trimmed.length === 0 ? null : trimmed;
}

/**
 * Create/edit a plant: all fields (design §3). The location picker is a native
 * `<select>` with a "No room (homeless)" option mapping to `location_id: null`;
 * `pot_material`/`light_level` are enum selects with the wire values. Client-side
 * required-name mirror of the server 422; surfaces server 422 (incl. the
 * unknown-location case) on the relevant field.
 */
export function PlantFormModal({
  plant,
  locations,
  onSubmit,
  onClose,
}: PlantFormModalProps): ReactNode {
  const isEdit = plant !== undefined;
  const [name, setName] = useState(plant?.name ?? "");
  const [species, setSpecies] = useState(plant?.species ?? "");
  const [locationId, setLocationId] = useState(
    plant?.location_id !== undefined && plant.location_id !== null
      ? String(plant.location_id)
      : HOMELESS_VALUE,
  );
  const [acquiredOn, setAcquiredOn] = useState(plant?.acquired_on ?? "");
  const [potSizeCm, setPotSizeCm] = useState(
    plant?.pot_size_cm !== undefined && plant.pot_size_cm !== null
      ? String(plant.pot_size_cm)
      : "",
  );
  const [potMaterial, setPotMaterial] = useState<string>(
    plant?.pot_material ?? "",
  );
  const [lightLevel, setLightLevel] = useState<string>(
    plant?.light_level ?? "",
  );
  const [notes, setNotes] = useState(plant?.notes ?? "");
  const [tags, setTags] = useState((plant?.tags ?? []).join(", "));
  const [archived, setArchived] = useState(plant?.archived ?? false);

  const [nameError, setNameError] = useState<string | null>(null);
  const [potSizeError, setPotSizeError] = useState<string | null>(null);
  const [locationError, setLocationError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  const acquiredOnId = useId();
  const potSizeId = useId();
  const archivedId = useId();

  const locationOptions = [
    { value: HOMELESS_VALUE, label: "No room (homeless)" },
    ...locations.map((room) => ({
      value: String(room.id),
      label: room.name,
    })),
  ];

  const potMaterialOptions = [
    { value: "", label: "Not set" },
    ...POT_MATERIALS.map((material) => ({ value: material, label: material })),
  ];

  const lightLevelOptions = [
    { value: "", label: "Not set" },
    ...LIGHT_LEVELS.map((level) => ({ value: level, label: level })),
  ];

  async function handleSubmit(): Promise<void> {
    if (name.trim().length === 0) {
      setNameError("Please enter a plant name.");
      return;
    }
    const trimmedPotSize = potSizeCm.trim();
    if (
      trimmedPotSize.length > 0 &&
      !Number.isInteger(Number(trimmedPotSize))
    ) {
      setPotSizeError("Pot size must be a whole number of centimeters.");
      return;
    }
    setNameError(null);
    setPotSizeError(null);
    setLocationError(null);
    setFormError(null);
    setSubmitting(true);

    const input: PlantInput = {
      name: name.trim(),
      species: orNull(species),
      location_id: locationId === HOMELESS_VALUE ? null : Number(locationId),
      acquired_on: orNull(acquiredOn),
      pot_size_cm: parseOptionalInt(potSizeCm),
      pot_material: potMaterial === "" ? null : (potMaterial as PotMaterial),
      light_level: lightLevel === "" ? null : (lightLevel as LightLevel),
      notes: orNull(notes),
      tags: parseTags(tags),
      archived,
    };

    try {
      await onSubmit(input);
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 422) {
        // 422 covers bad body AND the unknown-location body-reference case
        // (design §1). Surface it on the location field when a room is chosen,
        // otherwise on the name field; keep a form-level fallback too.
        if (locationId !== HOMELESS_VALUE) {
          setLocationError("The server rejected the selected room.");
        } else {
          setNameError("The server rejected this plant. Check the fields.");
        }
      } else {
        setFormError("Could not save this plant. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <Modal title={isEdit ? "Edit plant" : "Add plant"} onClose={onClose}>
      <form
        className="flex flex-col gap-4"
        // all validation is custom (consistent field errors, incl. the name
        // mirror); native bubbles would preempt it for step/min/max
        noValidate
        onSubmit={(event) => {
          event.preventDefault();
          void handleSubmit();
        }}
      >
        <TextField
          label="Name"
          value={name}
          onChange={setName}
          error={nameError ?? undefined}
          required
          maxLength={NAME_MAX}
          placeholder="e.g. Monstera"
          autoFocus
        />
        <TextField
          label="Species"
          value={species}
          onChange={setSpecies}
          maxLength={SPECIES_MAX}
          placeholder="Optional - e.g. Monstera deliciosa"
        />

        <FieldSelect
          label="Room"
          value={locationId}
          options={locationOptions}
          onChange={setLocationId}
        />
        {locationError ? (
          <p className="font-body text-sm text-danger" role="alert">
            {locationError}
          </p>
        ) : null}

        <div className="flex flex-col gap-1.5">
          <label htmlFor={acquiredOnId} className={LABEL_CLASSES}>
            Acquired on (optional)
          </label>
          <input
            id={acquiredOnId}
            type="date"
            className={SELECT_CLASSES}
            value={acquiredOn}
            aria-describedby={`${acquiredOnId}-hint`}
            onChange={(event) => {
              setAcquiredOn(event.target.value);
            }}
          />
          <p
            id={`${acquiredOnId}-hint`}
            className="font-body text-sm text-ink-muted"
          >
            Leave blank if you don&apos;t know.
          </p>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={potSizeId} className={LABEL_CLASSES}>
            Pot size (cm)
          </label>
          <input
            id={potSizeId}
            type="number"
            inputMode="numeric"
            min={POT_SIZE_MIN}
            max={POT_SIZE_MAX}
            step={1}
            className={SELECT_CLASSES}
            value={potSizeCm}
            placeholder="Optional"
            aria-invalid={potSizeError !== null || undefined}
            onChange={(event) => {
              setPotSizeCm(event.target.value);
            }}
          />
          {potSizeError ? (
            <p className="font-body text-sm text-danger" role="alert">
              {potSizeError}
            </p>
          ) : null}
        </div>

        <FieldSelect
          label="Pot material"
          value={potMaterial}
          options={potMaterialOptions}
          onChange={setPotMaterial}
        />
        <FieldSelect
          label="Light level"
          value={lightLevel}
          options={lightLevelOptions}
          onChange={setLightLevel}
        />

        <TextField
          label="Notes"
          value={notes}
          onChange={setNotes}
          multiline
          maxLength={NOTES_MAX}
          placeholder="Optional - light, watering, anything worth remembering."
        />
        <TextField
          label="Tags"
          value={tags}
          onChange={setTags}
          placeholder="Comma-separated, e.g. rare, fern"
        />

        <div className="flex items-center gap-2">
          <input
            id={archivedId}
            type="checkbox"
            className="min-h-tap-min min-w-tap-min accent-accent"
            checked={archived}
            onChange={(event) => {
              setArchived(event.target.checked);
            }}
          />
          <label htmlFor={archivedId} className={LABEL_CLASSES}>
            Archived
          </label>
        </div>

        {formError ? (
          <p className="font-body text-sm text-danger" role="alert">
            {formError}
          </p>
        ) : null}
        <div className="flex justify-end gap-2">
          <Button variant="ghost" onClick={onClose} disabled={submitting}>
            Cancel
          </Button>
          <Button type="submit" variant="primary" disabled={submitting}>
            {submitting ? "Saving..." : isEdit ? "Save changes" : "Add plant"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
