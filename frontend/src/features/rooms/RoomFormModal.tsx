import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { Modal } from "@/components/ui/Modal";
import { TextField } from "@/components/ui/TextField";
import { ApiError } from "@/lib/api/client";
import type { Location, LocationInput } from "@/lib/api/locations";

interface RoomFormModalProps {
  /** Existing room when editing; absent when creating. */
  readonly room?: Location | undefined;
  readonly onSubmit: (input: LocationInput) => Promise<void>;
  readonly onClose: () => void;
}

// Mirrors the server bounds (design §1): name 1..120, notes optional <=2000.
const NAME_MAX = 120;
const NOTES_MAX = 2000;

/** Create/edit a room. Client-side required-name mirror of the server 422; surfaces server errors. */
export function RoomFormModal({
  room,
  onSubmit,
  onClose,
}: RoomFormModalProps): ReactNode {
  const isEdit = room !== undefined;
  const [name, setName] = useState(room?.name ?? "");
  const [notes, setNotes] = useState(room?.notes ?? "");
  const [nameError, setNameError] = useState<string | null>(null);
  const [formError, setFormError] = useState<string | null>(null);
  const [submitting, setSubmitting] = useState(false);

  async function handleSubmit(): Promise<void> {
    // Client-side mirror of the server's name validator (fail fast on name).
    if (name.trim().length === 0) {
      setNameError("Please enter a room name.");
      return;
    }
    setNameError(null);
    setFormError(null);
    setSubmitting(true);
    const trimmedNotes = notes.trim();
    try {
      await onSubmit({
        name: name.trim(),
        notes: trimmedNotes.length === 0 ? null : trimmedNotes,
      });
      onClose();
    } catch (err: unknown) {
      if (err instanceof ApiError && err.status === 422) {
        setNameError("The server rejected this room name.");
      } else {
        setFormError("Could not save this room. Please try again.");
      }
      setSubmitting(false);
    }
  }

  return (
    <Modal title={isEdit ? "Edit room" : "Add room"} onClose={onClose}>
      <form
        className="flex flex-col gap-4"
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
          placeholder="e.g. Greenhouse"
          autoFocus
        />
        <TextField
          label="Notes"
          value={notes}
          onChange={setNotes}
          multiline
          maxLength={NOTES_MAX}
          placeholder="Optional - light, humidity, anything worth remembering."
        />
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
            {submitting ? "Saving..." : isEdit ? "Save changes" : "Add room"}
          </Button>
        </div>
      </form>
    </Modal>
  );
}
