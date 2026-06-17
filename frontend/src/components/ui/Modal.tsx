import { useEffect, useId, useRef } from "react";
import type { ReactNode } from "react";

interface ModalProps {
  readonly title: string;
  readonly onClose: () => void;
  readonly children: ReactNode;
}

/**
 * Accessible modal dialog (FE-001/FE-011): `role="dialog"`, `aria-modal`,
 * labelled by its title, Escape-to-close, and a backdrop click closes it.
 * Initial focus lands inside the dialog on open.
 */
export function Modal({ title, onClose, children }: ModalProps): ReactNode {
  const titleId = useId();
  const dialogRef = useRef<HTMLDivElement>(null);

  useEffect(() => {
    function onKeyDown(event: KeyboardEvent): void {
      if (event.key === "Escape") {
        onClose();
      }
    }
    document.addEventListener("keydown", onKeyDown);
    dialogRef.current?.focus();
    return () => {
      document.removeEventListener("keydown", onKeyDown);
    };
  }, [onClose]);

  return (
    <div
      className="fixed inset-0 z-50 flex items-end justify-center bg-overlay p-4 sm:items-center"
      onClick={onClose}
    >
      <div
        ref={dialogRef}
        role="dialog"
        aria-modal="true"
        aria-labelledby={titleId}
        tabIndex={-1}
        // Cap the height to the padded viewport (backdrop has p-4 = 2rem vertical)
        // and let the body scroll, so a tall form is never clipped above the
        // screen on a phone (BUG-003). dvh tracks the mobile browser chrome.
        className="flex max-h-[calc(100dvh-2rem)] w-full max-w-md flex-col gap-4 rounded-card border-card border-border bg-surface-raised p-5 shadow-raised outline-none"
        onClick={(event) => {
          event.stopPropagation();
        }}
      >
        <div className="flex shrink-0 items-center justify-between gap-3">
          <h2
            id={titleId}
            className="font-display text-2xl font-semibold text-ink"
          >
            {title}
          </h2>
          <button
            type="button"
            aria-label="Close"
            onClick={onClose}
            className="grid min-h-tap-min min-w-tap-min place-items-center rounded-control border-control border-transparent text-xl text-ink-muted hover:bg-surface-sunken hover:text-ink"
          >
            ✕
          </button>
        </div>
        <div className="min-h-0 flex-1 overflow-y-auto">{children}</div>
      </div>
    </div>
  );
}
