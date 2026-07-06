import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import type { Plant } from "@/lib/api/plants";

const TERM_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

interface PlantAttributesCardProps {
  readonly plant: Plant;
  /** Resolved room name; null when unknown or homeless (degrades to no row). */
  readonly locationName: string | null;
}

/** One label + value row; the caller only renders it when the value is set. */
function Row({
  label,
  children,
}: {
  readonly label: string;
  readonly children: ReactNode;
}): ReactNode {
  return (
    <div className="flex flex-col gap-0.5">
      <dt className={TERM_CLASSES}>{label}</dt>
      <dd className="font-body text-base text-ink break-words">{children}</dd>
    </div>
  );
}

/** "14 cm terracotta" / "14 cm" / "terracotta" - only the set parts (M-ATTR). */
function innerPotText(plant: Plant): string | null {
  const parts: string[] = [];
  if (plant.pot_size_cm !== null) {
    parts.push(`${String(plant.pot_size_cm)} cm`);
  }
  if (plant.pot_material !== null) {
    parts.push(plant.pot_material);
  }
  return parts.length > 0 ? parts.join(" ") : null;
}

/** Cachepot text; the material gates the row, the size gates its suffix (F-7). */
function outerPotText(plant: Plant): string | null {
  if (plant.outer_pot_material === null) {
    return null;
  }
  return plant.outer_pot_size_cm !== null
    ? `${plant.outer_pot_material} (${String(plant.outer_pot_size_cm)} cm)`
    : plant.outer_pot_material;
}

/**
 * The detail page's attributes card (US-4.3, AC1). Strictly omit-empty: a
 * field with no value renders NO row (never a blank/"null" value), and the
 * whole card is absent when nothing is set. The cachepot pair is gated on the
 * material, with the size suffix gated on the size (M-ATTR §3).
 */
export function PlantAttributesCard({
  plant,
  locationName,
}: PlantAttributesCardProps): ReactNode {
  const innerPot = innerPotText(plant);
  const outerPot = outerPotText(plant);
  const rows: readonly [string, ReactNode][] = [
    ["Species", plant.species],
    [
      "Room",
      locationName !== null && plant.location_id !== null ? (
        <Link
          to="/rooms"
          className="hover:text-accent-strong focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring"
        >
          {locationName}
        </Link>
      ) : null,
    ],
    ["Acquired", plant.acquired_on],
    ["Pot", innerPot],
    ["Outer pot", outerPot],
    ["Light", plant.light_level],
    ["Notes", plant.notes],
  ];
  const setRows = rows.filter(([, value]) => value !== null);
  const hasTags = plant.tags.length > 0;

  if (setRows.length === 0 && !hasTags) {
    return null;
  }

  return (
    <section
      aria-label="Plant details"
      className="rounded-card border-card border-border bg-surface-raised p-5 shadow-card"
    >
      <dl className="grid grid-cols-1 gap-4 sm:grid-cols-2">
        {setRows.map(([label, value]) => (
          <Row key={label} label={label}>
            {value}
          </Row>
        ))}
        {hasTags ? (
          <div className="flex flex-col gap-1.5 sm:col-span-2">
            <dt className={TERM_CLASSES}>Tags</dt>
            <dd>
              <ul className="flex flex-wrap gap-1.5">
                {plant.tags.map((tag) => (
                  <li
                    key={tag}
                    className="rounded-pill border-control border-border bg-surface px-2 py-0.5 font-label text-xs uppercase tracking-widest text-ink-muted break-words"
                  >
                    {tag}
                  </li>
                ))}
              </ul>
            </dd>
          </div>
        ) : null}
      </dl>
    </section>
  );
}
