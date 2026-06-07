import type { ReactNode } from "react";

import { HealthBadge } from "./HealthBadge";

interface StatPod {
  readonly value: string;
  readonly label: string;
  readonly tone: "neutral" | "due" | "late";
}

// Static placeholder figures for the walking skeleton; real counts arrive with
// the plant features (E2-E4).
const STAT_PODS: readonly StatPod[] = [
  { value: "24", label: "plants", tone: "neutral" },
  { value: "3", label: "due", tone: "due" },
  { value: "2", label: "late", tone: "late" },
];

function podToneClass(tone: StatPod["tone"]): string {
  switch (tone) {
    case "due":
      return "text-success";
    case "late":
      return "text-accent";
    case "neutral":
      return "text-ink";
  }
}

export function TodayPage(): ReactNode {
  return (
    <section className="flex flex-col gap-8">
      <header className="flex flex-col gap-6 sm:flex-row sm:items-end sm:justify-between">
        <div className="flex flex-col gap-2">
          <h1 className="max-w-[18ch] font-display text-4xl font-extrabold leading-tight text-ink sm:text-5xl">
            Today, the garden needs{" "}
            <span className="text-accent">a little love</span>.
          </h1>
          <p className="font-label text-sm uppercase tracking-wide text-ink-muted">
            What needs care will appear here once plants exist.
          </p>
        </div>

        <ul className="flex gap-3">
          {STAT_PODS.map((pod) => (
            <li
              key={pod.label}
              className="min-w-[5.5rem] rounded-card border-card border-border bg-surface-raised px-4 py-3 text-center shadow-card"
            >
              <div
                className={`font-display text-3xl font-extrabold leading-none ${podToneClass(
                  pod.tone,
                )}`}
              >
                {pod.value}
              </div>
              <div className="mt-1 font-label text-xs font-bold uppercase tracking-wide text-ink-muted">
                {pod.label}
              </div>
            </li>
          ))}
        </ul>
      </header>

      <HealthBadge />
    </section>
  );
}
