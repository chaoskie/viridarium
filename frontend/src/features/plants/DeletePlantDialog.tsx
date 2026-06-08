import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import type { Plant } from "@/lib/api/plants";

interface DeletePlantDialogProps {
  readonly plant: Plant;
  readonly onConfirm: (id: number) => Promise<void>;
  readonly onClose: () => void;
}

/** Plain confirm-delete dialog ([TEMPLATE] from `DeleteRoomDialog`). */
export function DeletePlantDialog({
  plant,
  onConfirm,
  onClose,
}: DeletePlantDialogProps): ReactNode {
  const [submitting, setSubmitting] = useState(false);
  const [error, setError] = useState<string | null>(null);

  async function handleConfirm(): Promise<void> {
    setSubmitting(true);
    setError(null);
    try {
      await onConfirm(plant.id);
      onClose();
    } catch {
      setError("Could not delete this plant. Please try again.");
      setSubmitting(false);
    }
  }

  return (
    <Modal title="Delete plant" onClose={onClose}>
      <p className="font-body text-base text-ink">
        Delete <span className="font-semibold">{plant.name}</span>? This cannot
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
