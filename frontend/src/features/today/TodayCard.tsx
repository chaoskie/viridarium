import { useState } from "react";
import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import { ApiError } from "@/lib/api/client";
import { createEvent, todayIsoDate } from "@/lib/api/careEvents";

import type { DueCareType, TodayCardModel } from "./buildTodayGroups";

export type { TodayCardModel } from "./buildTodayGroups";

interface TodayCardProps {
  /** The plant's card model (plant + due care types + worst overdue). */
  readonly card: TodayCardModel;
  /**
   * Called once the plant has nothing left due (every due care type logged) so
   * the page can drop the card from the list. Optional - the card already drops
   * satisfied care types in place.
   */
  readonly onAllCareLogged?: (plantId: number) => void;
}

type CareType = "water" | "feed";

/** Human label for a care type (capitalised button text). */
const CARE_LABEL: Record<CareType, string> = {
  water: "Water",
  feed: "Feed",
};

/** Turn any thrown value into friendly inline copy (mirrors useCareEvents). */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 422) {
      return "The server rejected this entry. Check the date and fields.";
    }
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/** "3 days overdue" / "1 day overdue" / "due today" - not colour-only (FE-011). */
function dueLabel(worstOverdue: number): string {
  if (worstOverdue <= 0) {
    return "due today";
  }
  const unit = worstOverdue === 1 ? "day" : "days";
  return `${String(worstOverdue)} ${unit} overdue`;
}

/**
 * One plant's Today card (US-4.1): a per-due-care-type Water/Feed button, plus a
 * Both button only when both water and feed are due. A tap logs the care
 * event(s) for today via the existing `createEvent` client; on success the
 * satisfied care type drops in place (no full reload), and when nothing is left
 * due the card asks the page to remove it (`onAllCareLogged`). Failures surface
 * inline and keep the card usable; buttons disable while a tap is in flight.
 */
export function TodayCard({
  card,
  onAllCareLogged,
}: TodayCardProps): ReactNode {
  // Locally tracked remaining due care types so a successful tap drops the
  // satisfied affordance in place without a parent reload (AC3).
  const [remaining, setRemaining] = useState<readonly DueCareType[]>(
    card.dueCareTypes,
  );
  const [busy, setBusy] = useState(false);
  const [error, setError] = useState<string | null>(null);

  const dueTypes = remaining.map((d) => d.care_type);
  const isOverdue = remaining.some((d) => d.overdue_days > 0);
  const worstOverdue = remaining.reduce(
    (worst, d) => Math.max(worst, d.overdue_days),
    0,
  );
  const bothDue = dueTypes.includes("water") && dueTypes.includes("feed");

  async function logTypes(types: readonly CareType[]): Promise<void> {
    setBusy(true);
    setError(null);
    const happened_on = todayIsoDate();
    // Track which types actually persisted so a partial "Both" failure drops
    // only the succeeded type(s) - a re-tap must not duplicate a logged event.
    const succeeded: CareType[] = [];
    try {
      for (const type of types) {
        await createEvent(card.plant.id, { type, happened_on });
        succeeded.push(type);
      }
      const next = remaining.filter((d) => !succeeded.includes(d.care_type));
      setRemaining(next);
      if (next.length === 0) {
        onAllCareLogged?.(card.plant.id);
      }
    } catch (err: unknown) {
      setRemaining((prev) =>
        prev.filter((d) => !succeeded.includes(d.care_type)),
      );
      setError(toMessage(err));
    } finally {
      setBusy(false);
    }
  }

  // Marker glyph + label make the overdue/due-today distinction non-colour-only.
  const markerGlyph = isOverdue ? "⚠" : "•"; // ⚠ vs •

  return (
    <li className="flex flex-col gap-3 border-card border-border bg-surface-raised p-4 shadow-card sm:flex-row sm:items-center sm:justify-between">
      <div className="flex flex-col gap-1">
        <h3 className="font-display text-xl font-semibold text-ink">
          {card.plant.name}
        </h3>
        <p
          className={
            isOverdue
              ? "flex items-center gap-1.5 font-label text-xs font-semibold uppercase tracking-widest text-accent-strong"
              : "flex items-center gap-1.5 font-label text-xs font-semibold uppercase tracking-widest text-ink-muted"
          }
        >
          <span aria-hidden="true">{markerGlyph}</span>
          <span>{dueLabel(worstOverdue)}</span>
        </p>
      </div>

      <div className="flex flex-col items-start gap-1.5 sm:items-end">
        <div className="flex flex-wrap gap-2">
          {dueTypes.includes("water") ? (
            <Button
              variant="ghost"
              aria-label={`Water ${card.plant.name}`}
              disabled={busy}
              onClick={() => {
                void logTypes(["water"]);
              }}
            >
              {CARE_LABEL.water}
            </Button>
          ) : null}
          {dueTypes.includes("feed") ? (
            <Button
              variant="ghost"
              aria-label={`Feed ${card.plant.name}`}
              disabled={busy}
              onClick={() => {
                void logTypes(["feed"]);
              }}
            >
              {CARE_LABEL.feed}
            </Button>
          ) : null}
          {bothDue ? (
            <Button
              variant="primary"
              aria-label={`Both ${card.plant.name}`}
              disabled={busy}
              onClick={() => {
                void logTypes(["water", "feed"]);
              }}
            >
              Both
            </Button>
          ) : null}
        </div>
        {error !== null ? (
          <p role="alert" className="font-body text-sm text-danger">
            {error}
          </p>
        ) : null}
      </div>
    </li>
  );
}
