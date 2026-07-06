import type { ReactNode } from "react";

import { Button } from "@/components/ui/Button";
import type { ScheduleDue } from "@/lib/api/plants";

interface PlantSchedulesCardProps {
  readonly schedules: readonly ScheduleDue[];
  /** Opens the schedule setup (the existing `CareScheduleModal`). */
  readonly onSetup: () => void;
}

const CARE_LABELS: Record<ScheduleDue["care_type"], string> = {
  water: "Water",
  feed: "Feed",
};

/** "3 days overdue" / "1 day overdue" (mirrors the Today card, FE-011). */
function overdueLabel(days: number): string {
  return `${String(days)} ${days === 1 ? "day" : "days"} overdue`;
}

/**
 * One schedule's due state: paused (null `next_due` - reason, no date), overdue
 * (date + non-colour-only emphasis, Today-view tokens), or due (date only).
 * The both-null invariant means a paused row never shows an overdue badge.
 */
function ScheduleRow({ due }: { readonly due: ScheduleDue }): ReactNode {
  const overdue = due.next_due !== null && (due.overdue_days ?? 0) > 0;
  return (
    <li className="flex flex-wrap items-center justify-between gap-2">
      <span className="font-label text-xs font-semibold uppercase tracking-widest text-ink-muted">
        {CARE_LABELS[due.care_type]}
      </span>
      {due.next_due === null ? (
        <span className="font-body text-sm text-ink-muted">
          Paused for now - no upcoming date
        </span>
      ) : (
        <span
          className={
            overdue
              ? "flex items-center gap-1.5 font-label text-xs font-semibold uppercase tracking-widest text-accent-strong"
              : "flex items-center gap-1.5 font-body text-sm text-ink"
          }
        >
          <span aria-hidden="true">{overdue ? "⚠" : "•"}</span>
          <time className="font-mono">{due.next_due}</time>
          {overdue && due.overdue_days !== null ? (
            <span>{overdueLabel(due.overdue_days)}</span>
          ) : null}
        </span>
      )}
    </li>
  );
}

/**
 * The detail page's care schedules card (US-4.3, AC2): one row per enabled
 * schedule with its next-due state (M-SCHED §4), or an empty state with a
 * setup affordance when the plant has no schedules.
 */
export function PlantSchedulesCard({
  schedules,
  onSetup,
}: PlantSchedulesCardProps): ReactNode {
  return (
    <section
      aria-label="Care schedules"
      className="flex flex-col gap-3 rounded-card border-card border-border bg-surface-raised p-5 shadow-card"
    >
      <h2 className="font-display text-xl font-semibold text-ink">
        Care schedules
      </h2>
      {schedules.length === 0 ? (
        <div className="flex flex-col items-start gap-2">
          <p className="font-body text-base text-ink-muted">
            No care schedules yet.
          </p>
          <Button variant="ghost" onClick={onSetup}>
            Set up a schedule
          </Button>
        </div>
      ) : (
        <ul className="flex flex-col gap-2">
          {schedules.map((due) => (
            <ScheduleRow key={due.care_type} due={due} />
          ))}
        </ul>
      )}
    </section>
  );
}
