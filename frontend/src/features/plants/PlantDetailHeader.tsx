import type { ReactNode } from "react";
import { Link } from "react-router-dom";

import { Button } from "@/components/ui/Button";
import type { Plant } from "@/lib/api/plants";

interface PlantDetailHeaderProps {
  readonly plant: Plant;
  readonly onEdit: () => void;
  readonly onLogCare: () => void;
  readonly onSchedules: () => void;
  readonly onPhotos: () => void;
  readonly onDelete: () => void;
}

const BACK_LINK_CLASSES =
  "inline-flex min-h-tap-min items-center gap-1.5 font-label text-xs font-semibold uppercase tracking-widest text-ink-muted hover:text-ink";

/**
 * The detail page's header (US-4.3): back link, plant name, species, archived
 * badge, and the action row wiring the existing modals (edit / log care /
 * schedules / photos / delete). Every button carries an accessible name
 * (FE-011); behaviour lives in the page's handlers.
 */
export function PlantDetailHeader({
  plant,
  onEdit,
  onLogCare,
  onSchedules,
  onPhotos,
  onDelete,
}: PlantDetailHeaderProps): ReactNode {
  return (
    <header className="flex flex-col gap-3">
      <Link to="/plants" className={BACK_LINK_CLASSES}>
        <span aria-hidden="true">←</span>
        Back to plants
      </Link>
      <div className="flex flex-wrap items-center gap-2">
        <h1 className="font-display text-4xl font-extrabold text-ink break-words">
          {plant.name}
        </h1>
        {plant.archived ? (
          <span className="rounded-pill border-control border-border bg-surface-sunken px-2 py-0.5 font-label text-xs uppercase tracking-widest text-ink-muted">
            Archived
          </span>
        ) : null}
      </div>
      {plant.species !== null && plant.species.length > 0 ? (
        <p className="font-mono text-base italic text-ink-muted break-words">
          {plant.species}
        </p>
      ) : null}
      <div className="flex flex-wrap gap-2">
        <Button
          variant="primary"
          aria-label={`Log care for ${plant.name}`}
          onClick={onLogCare}
        >
          Log care
        </Button>
        <Button
          variant="ghost"
          aria-label={`Edit ${plant.name}`}
          onClick={onEdit}
        >
          Edit
        </Button>
        <Button
          variant="ghost"
          aria-label={`Configure care schedules for ${plant.name}`}
          onClick={onSchedules}
        >
          Schedules
        </Button>
        <Button
          variant="ghost"
          aria-label={`View photos of ${plant.name}`}
          onClick={onPhotos}
        >
          Photos
        </Button>
        <Button
          variant="danger"
          aria-label={`Delete ${plant.name}`}
          onClick={onDelete}
        >
          Delete
        </Button>
      </div>
    </header>
  );
}
