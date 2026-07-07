import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { useNavigate, useParams } from "react-router-dom";

import { fetchLocations, type Location } from "@/lib/api/locations";
import {
  deletePlant,
  updatePlant,
  type Plant,
  type PlantInput,
} from "@/lib/api/plants";

import { CareTimeline } from "./CareTimeline";
import { CareScheduleModal } from "./CareScheduleModal";
import { DeletePlantDialog } from "./DeletePlantDialog";
import { LogCareModal } from "./LogCareModal";
import { PhotoGalleryModal } from "./PhotoGalleryModal";
import { PlantAttributesCard } from "./PlantAttributesCard";
import { PlantDetailHeader } from "./PlantDetailHeader";
import { PlantFormModal } from "./PlantFormModal";
import { PlantGallery } from "./PlantGallery";
import { PlantSchedulesCard } from "./PlantSchedulesCard";
import { usePlantDetail } from "./usePlantDetail";

type ModalState =
  | { readonly kind: "closed" }
  | { readonly kind: "edit" }
  | { readonly kind: "log" }
  | { readonly kind: "schedules" }
  | { readonly kind: "photos" }
  | { readonly kind: "delete" };

/**
 * The full plant detail page (US-4.3): header + attributes + schedules +
 * gallery + the existing `CareTimeline`, with the already-built modals wired
 * for edit / log care / schedules / photos / delete. A thin orchestrator: the
 * sections are their own components; this page owns the state machine, the
 * modal switch, and the after-mutation `reload()` (foundation §1: owned
 * handlers for edit/log/delete, close-signal for the self-managing modals).
 */
export function PlantDetailPage(): ReactNode {
  const params = useParams<{ id: string }>();
  const navigate = useNavigate();
  const plantId = Number(params.id);
  const { state, reload } = usePlantDetail(plantId);

  const [modal, setModal] = useState<ModalState>({ kind: "closed" });
  const [rooms, setRooms] = useState<readonly Location[]>([]);
  // Remounts the timeline + gallery after a care/photo mutation (design §behaviour).
  const [refreshKey, setRefreshKey] = useState(0);

  useEffect(() => {
    let active = true;
    void fetchLocations()
      .then((loaded) => {
        if (active) {
          setRooms(loaded);
        }
      })
      .catch(() => {
        // The room name degrades gracefully; the page still works.
        if (active) {
          setRooms([]);
        }
      });
    return () => {
      active = false;
    };
  }, []);

  function closeModal(): void {
    setModal({ kind: "closed" });
  }

  /** Close a self-managing modal (schedules/photos): its close IS the mutation signal. */
  function closeAndReload(bumpKey: boolean): void {
    closeModal();
    void reload();
    if (bumpKey) {
      setRefreshKey((key) => key + 1);
    }
  }

  async function handleEditSubmit(
    plant: Plant,
    input: PlantInput,
  ): Promise<void> {
    await updatePlant(plant.id, input);
    await reload();
  }

  async function handleDeleteConfirm(id: number): Promise<void> {
    await deletePlant(id);
    void navigate("/plants");
  }

  if (state.kind === "loading") {
    return (
      <p
        className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card"
        aria-live="polite"
      >
        Loading plant...
      </p>
    );
  }

  if (state.kind === "error") {
    return (
      <p
        className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-ink-muted shadow-card"
        role="alert"
      >
        That plant could not be found.
      </p>
    );
  }

  const plant = state.plant;
  const locationName =
    rooms.find((room) => room.id === plant.location_id)?.name ?? null;

  return (
    <section className="flex flex-col gap-6">
      <PlantDetailHeader
        plant={plant}
        onEdit={() => {
          setModal({ kind: "edit" });
        }}
        onLogCare={() => {
          setModal({ kind: "log" });
        }}
        onSchedules={() => {
          setModal({ kind: "schedules" });
        }}
        onPhotos={() => {
          setModal({ kind: "photos" });
        }}
        onDelete={() => {
          setModal({ kind: "delete" });
        }}
      />

      <PlantAttributesCard plant={plant} locationName={locationName} />

      <PlantSchedulesCard
        schedules={plant.schedules}
        onSetup={() => {
          setModal({ kind: "schedules" });
        }}
      />

      <PlantGallery
        key={`gallery-${String(refreshKey)}`}
        plant={plant}
        onOpen={() => {
          setModal({ kind: "photos" });
        }}
      />

      <CareTimeline key={`timeline-${String(refreshKey)}`} plantId={plant.id} />

      {modal.kind === "edit" ? (
        <PlantFormModal
          plant={plant}
          locations={rooms}
          onSubmit={(input) => handleEditSubmit(plant, input)}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "log" ? (
        <LogCareModal
          plant={plant}
          onLogged={() => {
            void reload();
            setRefreshKey((key) => key + 1);
          }}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "schedules" ? (
        <CareScheduleModal
          plant={plant}
          onClose={() => {
            closeAndReload(false);
          }}
        />
      ) : null}

      {modal.kind === "photos" ? (
        <PhotoGalleryModal
          plant={plant}
          onClose={() => {
            closeAndReload(true);
          }}
        />
      ) : null}

      {modal.kind === "delete" ? (
        <DeletePlantDialog
          plant={plant}
          onConfirm={handleDeleteConfirm}
          onClose={closeModal}
        />
      ) : null}
    </section>
  );
}
