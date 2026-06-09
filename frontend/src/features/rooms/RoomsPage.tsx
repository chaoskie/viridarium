import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import type { Location } from "@/lib/api/locations";

import { DeleteRoomDialog } from "./DeleteRoomDialog";
import { RoomFormModal } from "./RoomFormModal";
import { useLocations } from "./useLocations";

type ModalState =
  | { readonly kind: "closed" }
  | { readonly kind: "create" }
  | { readonly kind: "edit"; readonly room: Location }
  | { readonly kind: "delete"; readonly room: Location };

export function RoomsPage(): ReactNode {
  const { locations, loading, error, create, update, remove } = useLocations();
  const [modal, setModal] = useState<ModalState>({ kind: "closed" });

  function closeModal(): void {
    setModal({ kind: "closed" });
  }

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-wrap items-center justify-between gap-3">
        <h1 className="font-display text-4xl font-extrabold text-ink">Rooms</h1>
        <Button
          variant="primary"
          onClick={() => {
            setModal({ kind: "create" });
          }}
        >
          Add room
        </Button>
      </header>

      {loading ? (
        <p
          className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card"
          aria-live="polite"
        >
          Loading rooms...
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

      {!loading && error === null && locations.length === 0 ? (
        <p className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-ink-muted shadow-card">
          No rooms yet. Add your first room to start organising your plants.
        </p>
      ) : null}

      {!loading && error === null && locations.length > 0 ? (
        <ul className="flex flex-col gap-3">
          {locations.map((room) => (
            <li
              key={room.id}
              className="flex flex-col gap-3 rounded-card border-card border-border bg-surface-raised p-4 shadow-card sm:flex-row sm:items-center sm:justify-between"
            >
              <div className="flex flex-col gap-1">
                <h2 className="font-display text-xl font-semibold text-ink">
                  {room.name}
                </h2>
                {room.notes !== null && room.notes.length > 0 ? (
                  <p className="font-mono text-base italic text-ink-muted">
                    {room.notes}
                  </p>
                ) : null}
              </div>
              <div className="flex shrink-0 gap-2">
                <Button
                  variant="ghost"
                  aria-label={`Edit ${room.name}`}
                  onClick={() => {
                    setModal({ kind: "edit", room });
                  }}
                >
                  Edit
                </Button>
                <Button
                  variant="danger"
                  aria-label={`Delete ${room.name}`}
                  onClick={() => {
                    setModal({ kind: "delete", room });
                  }}
                >
                  Delete
                </Button>
              </div>
            </li>
          ))}
        </ul>
      ) : null}

      {modal.kind === "create" ? (
        <RoomFormModal onSubmit={create} onClose={closeModal} />
      ) : null}

      {modal.kind === "edit" ? (
        <RoomFormModal
          room={modal.room}
          onSubmit={(input) => update(modal.room.id, input)}
          onClose={closeModal}
        />
      ) : null}

      {modal.kind === "delete" ? (
        <DeleteRoomDialog
          room={modal.room}
          onConfirm={remove}
          onClose={closeModal}
        />
      ) : null}
    </section>
  );
}
