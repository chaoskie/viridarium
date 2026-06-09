import { useCallback, useEffect, useId, useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { fetchLocations, type Location } from "@/lib/api/locations";
import type { Plant, PlantFilter } from "@/lib/api/plants";
import { fetchPhotos, photoUrl } from "@/lib/api/photos";

import { DeletePlantDialog } from "./DeletePlantDialog";
import { PhotoGalleryModal } from "./PhotoGalleryModal";
import { PlantFormModal } from "./PlantFormModal";
import { usePlants } from "./usePlants";

type ModalState =
  | { readonly kind: "closed" }
  | { readonly kind: "create" }
  | { readonly kind: "edit"; readonly plant: Plant }
  | { readonly kind: "delete"; readonly plant: Plant }
  | { readonly kind: "photos"; readonly plant: Plant };

/**
 * A small, self-contained cover thumbnail for a plant card. Fetches the plant's
 * photos lazily on mount (so it never blocks the list render) and shows the
 * `is_cover` image, or a neutral placeholder when there is none / the fetch
 * fails. Deliberately simple: no shared state, no ret-on-error.
 */
function CoverThumb({ plant }: { readonly plant: Plant }): ReactNode {
  const [coverId, setCoverId] = useState<number | null>(null);

  useEffect(() => {
    let active = true;
    void fetchPhotos(plant.id)
      .then((photos) => {
        if (active) {
          const cover = photos.find((photo) => photo.is_cover);
          setCoverId(cover?.id ?? null);
        }
      })
      .catch(() => {
        if (active) {
          setCoverId(null);
        }
      });
    return () => {
      active = false;
    };
  }, [plant.id]);

  if (coverId === null) {
    return (
      <div
        className="grid h-16 w-16 shrink-0 place-items-center rounded-control border-control border-border bg-surface-sunken font-label text-xs uppercase tracking-widest text-ink-muted"
        aria-hidden="true"
      >
        No photo
      </div>
    );
  }
  return (
    <img
      src={photoUrl(plant.id, coverId)}
      alt={`${plant.name} cover photo`}
      loading="lazy"
      className="h-16 w-16 shrink-0 rounded-control border-control border-border object-cover"
    />
  );
}

const CONTROL_CLASSES =
  "min-h-tap-min w-full rounded-control border-control border-border bg-surface px-3 py-2 font-body text-base text-ink placeholder:text-ink-muted focus-visible:outline focus-visible:outline-2 focus-visible:outline-ring";

const LABEL_CLASSES =
  "font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

const HOMELESS_VALUE = "homeless";
const ALL_VALUE = "";

/** Archive-scope choice for the list view (US-2.4). Default `active`. */
type PlantView = "active" | "archived" | "all";

/** Build the `PlantFilter` from the current control state (empties dropped). */
function buildFilter(
  q: string,
  locationChoice: string,
  tag: string,
  species: string,
  view: PlantView,
): PlantFilter {
  // Build incrementally so unset fields stay absent (exactOptionalPropertyTypes).
  const filter: {
    q?: string;
    location_id?: number;
    tag?: string;
    species?: string;
    homeless?: boolean;
    archived?: boolean;
    include_archived?: boolean;
  } = {};
  if (q.trim().length > 0) {
    filter.q = q.trim();
  }
  if (tag.trim().length > 0) {
    filter.tag = tag.trim();
  }
  if (species.trim().length > 0) {
    filter.species = species.trim();
  }
  if (locationChoice === HOMELESS_VALUE) {
    filter.homeless = true;
  } else if (locationChoice !== ALL_VALUE) {
    filter.location_id = Number(locationChoice);
  }
  // active -> neither param (API default); archived -> archived only;
  // all -> include_archived overrides the scope (A2).
  if (view === "archived") {
    filter.archived = true;
  } else if (view === "all") {
    filter.include_archived = true;
  }
  return filter;
}

export function PlantsPage(): ReactNode {
  const {
    plants,
    loading,
    error,
    reload,
    create,
    update,
    remove,
    archive,
    unarchive,
  } = usePlants();
  const [rooms, setRooms] = useState<readonly Location[]>([]);
  const [modal, setModal] = useState<ModalState>({ kind: "closed" });

  const [q, setQ] = useState("");
  const [locationChoice, setLocationChoice] = useState(ALL_VALUE);
  const [tag, setTag] = useState("");
  const [species, setSpecies] = useState("");
  const [view, setView] = useState<PlantView>("active");

  const qId = useId();
  const locationId = useId();
  const tagId = useId();
  const speciesId = useId();
  const viewId = useId();

  useEffect(() => {
    let active = true;
    void fetchLocations()
      .then((loaded) => {
        if (active) {
          setRooms(loaded);
        }
      })
      .catch(() => {
        // Room names degrade gracefully; the list and filter still work.
        if (active) {
          setRooms([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  const roomName = useCallback(
    (id: number | null): string | null => {
      if (id === null) {
        return null;
      }
      const match = rooms.find((room) => room.id === id);
      return match?.name ?? null;
    },
    [rooms],
  );

  function applyFilter(): void {
    void reload(buildFilter(q, locationChoice, tag, species, view));
  }

  function closeModal(): void {
    setModal({ kind: "closed" });
  }

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-4xl font-extrabold text-ink">
          Plants
        </h1>
        <Button
          variant="primary"
          onClick={() => {
            setModal({ kind: "create" });
          }}
        >
          Add plant
        </Button>
      </header>

      <form
        className="grid grid-cols-1 gap-3 rounded-card border-card border-border bg-surface-raised p-4 shadow-card sm:grid-cols-2 lg:grid-cols-6"
        onSubmit={(event) => {
          event.preventDefault();
          applyFilter();
        }}
        aria-label="Search and filter plants"
      >
        <div className="flex flex-col gap-1.5">
          <label htmlFor={qId} className={LABEL_CLASSES}>
            Search
          </label>
          <input
            id={qId}
            type="search"
            className={CONTROL_CLASSES}
            value={q}
            placeholder="Name or species"
            onChange={(event) => {
              setQ(event.target.value);
            }}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={locationId} className={LABEL_CLASSES}>
            Room
          </label>
          <select
            id={locationId}
            className={CONTROL_CLASSES}
            value={locationChoice}
            onChange={(event) => {
              const next = event.target.value;
              setLocationChoice(next);
              void reload(buildFilter(q, next, tag, species, view));
            }}
          >
            <option value={ALL_VALUE}>All rooms</option>
            <option value={HOMELESS_VALUE}>Homeless</option>
            {rooms.map((room) => (
              <option key={room.id} value={String(room.id)}>
                {room.name}
              </option>
            ))}
          </select>
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={tagId} className={LABEL_CLASSES}>
            Tag
          </label>
          <input
            id={tagId}
            type="text"
            className={CONTROL_CLASSES}
            value={tag}
            placeholder="e.g. rare"
            onChange={(event) => {
              setTag(event.target.value);
            }}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={speciesId} className={LABEL_CLASSES}>
            Species
          </label>
          <input
            id={speciesId}
            type="text"
            className={CONTROL_CLASSES}
            value={species}
            placeholder="e.g. ficus"
            onChange={(event) => {
              setSpecies(event.target.value);
            }}
          />
        </div>

        <div className="flex flex-col gap-1.5">
          <label htmlFor={viewId} className={LABEL_CLASSES}>
            Show
          </label>
          <select
            id={viewId}
            className={CONTROL_CLASSES}
            value={view}
            onChange={(event) => {
              const next = event.target.value as PlantView;
              setView(next);
              void reload(buildFilter(q, locationChoice, tag, species, next));
            }}
          >
            <option value="active">Active</option>
            <option value="archived">Archived</option>
            <option value="all">All</option>
          </select>
        </div>

        <div className="flex items-end">
          <Button type="submit" variant="ghost" className="w-full">
            Apply
          </Button>
        </div>
      </form>

      {loading ? (
        <p
          className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card"
          aria-live="polite"
        >
          Loading plants...
        </p>
      ) : null}

      {!loading && error !== null ? (
        <p
          className="rounded-card border-card border-danger bg-surface-raised p-5 font-body text-base text-danger shadow-card"
          role="alert"
        >
          {error}
        </p>
      ) : null}

      {!loading && error === null && plants.length === 0 ? (
        <p className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-ink-muted shadow-card">
          No plants match. Add a plant or adjust your search.
        </p>
      ) : null}

      {!loading && error === null && plants.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {plants.map((plant) => {
            const room = roomName(plant.location_id);
            return (
              <li
                key={plant.id}
                className="flex flex-col gap-3 rounded-card border-card border-border bg-surface-raised p-4 shadow-card sm:flex-row sm:items-center sm:justify-between"
              >
                <div className="flex items-center gap-3">
                  <CoverThumb plant={plant} />
                  <div className="flex flex-col gap-1.5">
                    <div className="flex flex-wrap items-center gap-2">
                      <h2 className="font-display text-xl font-semibold text-ink">
                        {plant.name}
                      </h2>
                      {plant.archived ? (
                        <span className="rounded-pill border-control border-border bg-surface-sunken px-2 py-0.5 font-label text-xs uppercase tracking-widest text-ink-muted">
                          Archived
                        </span>
                      ) : null}
                    </div>
                    {plant.species !== null && plant.species.length > 0 ? (
                      <p className="font-mono text-base italic text-ink-muted">
                        {plant.species}
                      </p>
                    ) : null}
                    <p className="font-body text-sm text-ink-muted">
                      {room !== null ? room : "Homeless"}
                    </p>
                    {plant.tags.length > 0 ? (
                      <ul className="flex flex-wrap gap-1.5">
                        {plant.tags.map((t) => (
                          <li
                            key={t}
                            className="rounded-pill border-control border-border bg-surface px-2 py-0.5 font-label text-xs uppercase tracking-widest text-ink-muted"
                          >
                            {t}
                          </li>
                        ))}
                      </ul>
                    ) : null}
                  </div>
                </div>
                <div className="flex shrink-0 flex-wrap gap-2">
                  <Button
                    variant="ghost"
                    aria-label={`View photos of ${plant.name}`}
                    onClick={() => {
                      setModal({ kind: "photos", plant });
                    }}
                  >
                    Photos
                  </Button>
                  <Button
                    variant="ghost"
                    aria-label={`${plant.archived ? "Unarchive" : "Archive"} ${plant.name}`}
                    onClick={() => {
                      // Reversible (A4) - no confirm dialog.
                      void (plant.archived
                        ? unarchive(plant.id)
                        : archive(plant.id));
                    }}
                  >
                    {plant.archived ? "Unarchive" : "Archive"}
                  </Button>
                  <Button
                    variant="ghost"
                    aria-label={`Edit ${plant.name}`}
                    onClick={() => {
                      setModal({ kind: "edit", plant });
                    }}
                  >
                    Edit
                  </Button>
                  <Button
                    variant="danger"
                    aria-label={`Delete ${plant.name}`}
                    onClick={() => {
                      setModal({ kind: "delete", plant });
                    }}
                  >
                    Delete
                  </Button>
                </div>
              </li>
            );
          })}
        </ul>
      ) : null}

      {modal.kind === "create" ? (
        <PlantFormModal
          locations={rooms}
          onSubmit={create}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "edit" ? (
        <PlantFormModal
          plant={modal.plant}
          locations={rooms}
          onSubmit={(input) => update(modal.plant.id, input)}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "delete" ? (
        <DeletePlantDialog
          plant={modal.plant}
          onConfirm={remove}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "photos" ? (
        <PhotoGalleryModal plant={modal.plant} onClose={closeModal} />
      ) : null}
    </section>
  );
}
