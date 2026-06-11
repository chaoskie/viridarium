import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import {
  todayIsoDate,
  type CareEvent,
  type CareEventType,
} from "@/lib/api/careEvents";
import type { Plant } from "@/lib/api/plants";

import { LogCareModal } from "./LogCareModal";
import { useCareEvents } from "./useCareEvents";

interface QuickCareActionsProps {
  /** The plant this card's quick actions log events for. */
  readonly plant: Plant;
}

const FEEDBACK_LABELS: Record<CareEventType, string> = {
  water: "water",
  feed: "feed",
  repot: "repot",
  observe: "observation",
};

/**
 * Per-card care logging (US-3.2, AC1): one-tap "Water" / "Feed" buttons that
 * POST today's event with inline confirmation, plus the "Log care" entry to
 * the expanded `LogCareModal`. Self-contained (own modal + feedback state) so
 * `PlantsPage` stays thin - its oversize is filed debt. Errors are
 * non-blocking: surfaced inline, the buttons stay usable.
 */
export function QuickCareActions({ plant }: QuickCareActionsProps): ReactNode {
  const { error, log } = useCareEvents(plant.id);
  const [feedback, setFeedback] = useState<string | null>(null);
  const [modalOpen, setModalOpen] = useState(false);

  function confirmLogged(event: CareEvent): void {
    setFeedback(`Logged ${FEEDBACK_LABELS[event.type]} (${event.happened_on})`);
  }

  async function quickTap(type: "water" | "feed"): Promise<void> {
    setFeedback(null);
    const created = await log({ type, happened_on: todayIsoDate() });
    if (created !== null) {
      confirmLogged(created);
    }
  }

  return (
    <div className="flex flex-col items-start gap-1.5 sm:items-end">
      <div className="flex flex-wrap gap-2">
        <Button
          variant="ghost"
          aria-label={`Log water for ${plant.name} today`}
          onClick={() => {
            void quickTap("water");
          }}
        >
          Water
        </Button>
        <Button
          variant="ghost"
          aria-label={`Log feed for ${plant.name} today`}
          onClick={() => {
            void quickTap("feed");
          }}
        >
          Feed
        </Button>
        <Button
          variant="ghost"
          aria-label={`Log care for ${plant.name}`}
          onClick={() => {
            setFeedback(null);
            setModalOpen(true);
          }}
        >
          Log care
        </Button>
      </div>

      {feedback !== null ? (
        <p
          role="status"
          className="font-label text-xs uppercase tracking-widest text-accent"
        >
          {feedback}
        </p>
      ) : null}
      {error !== null ? (
        <p role="alert" className="font-body text-sm text-danger">
          {error}
        </p>
      ) : null}

      {modalOpen ? (
        <LogCareModal
          plant={plant}
          onLogged={confirmLogged}
          onClose={() => {
            setModalOpen(false);
          }}
        />
      ) : null}
    </div>
  );
}
