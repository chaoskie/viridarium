import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type { Location } from "@/lib/api/locations";

interface DeleteRoomDialogProps {
  readonly room: Location;
  readonly onConfirm: (id: number) => Promise<void>;
  readonly onClose: () => void;
}

/**
 * Plain confirm-delete dialog.
 *
 * NOTE: This is the unguarded delete for US-2.2 (no plants exist yet).
 * US-2.1 introduces the plant-aware flow (D-009): when a room holds plants,
 * the maintainer-approved homeless/reassign decision replaces this plain
 * confirm. Keep this component the single delete entry-point so that flow
 * slots in here without touching RoomsPage.
 */
export function DeleteRoomDialog({
  room,
  onConfirm,
  onClose,
}: DeleteRoomDialogProps): ReactNode {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm(): Promise<void> {
    setSubmitting(true);
    setError(null);
    try {
      await onConfirm(room.id);
      onClose();
    } catch {
      setError("Could not delete this room. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Delete room" onClose={onClose}>
      <p className="font-body text-base text-ink">
        Delete <span className="font-semibold">{room.name}</span>? This cannot
        be undone.
      </p>
      {error ? (
        <p className="font-body text-sm text-danger" role="alert">
          {error}
        </p>
      ) : null}
      <div className="flex justify-end gap-2">
        <Button variant="ghost" onClick={onClose} disabled={submitting}>
          Cancel
        </Button>
        <Button
          variant="danger"
          onClick={() => {
            void handleConfirm();
          }}
          disabled={submitting}
        >
          {submitting ? "Deleting..." : "Delete"}
        </Button>
      </div>
    </Modal>
  );
}
