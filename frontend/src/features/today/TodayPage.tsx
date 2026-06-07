import type { ReactNode } from "react";

import { HealthBadge } from "./HealthBadge";

interface StatPod {
  readonly value: string;
  readonly label: string;
  readonly tone: "neutral" | "due" | "late";
}

// Static placeholder figures for the walking skeleton; real counts arrive with
// the plant features (E2-E4). Labels are plain English per D-008.
const STAT_PODS: readonly StatPod[] = [
  { value: "24", label: "Plants", tone: "neutral" },
  { value: "3", label: "Due today", tone: "due" },
  { value: "2", label: "Overdue", tone: "late" },
];

interface CareCard {
  readonly name: string;
  readonly species: string;
  readonly room: string;
  readonly task: "Water" | "Feed";
  readonly status: "Overdue" | "Due today";
  readonly when: string;
}

// Placeholder care items echoing the dashboard's intent; all functional text in
// English (statuses, rooms, tasks) per D-008. Latin stays decorative only.
const CARE_CARDS: readonly CareCard[] = [
  {
    name: "Monstera",
    species: "Monstera deliciosa",
    room: "Living room",
    task: "Water",
    status: "Overdue",
    when: "2 days overdue",
  },
  {
    name: "Fiddle-leaf fig",
    species: "Ficus lyrata",
    room: "Study",
    task: "Water",
    status: "Overdue",
    when: "1 day overdue",
  },
  {
    name: "Moth orchid",
    species: "Phalaenopsis",
    room: "Kitchen",
    task: "Feed",
    status: "Due today",
    when: "Due today",
  },
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

function statusClass(status: CareCard["status"]): string {
  // Small pill text -> use the *-strong tones so every theme clears AA 4.5:1.
  return status === "Overdue"
    ? "border-accent text-accent-strong"
    : "border-accent-2 text-accent-2-strong";
}

export function TodayPage(): ReactNode {
  return (
    <section className="flex flex-col gap-8">
      <header className="flex flex-col gap-6 lg:flex-row lg:items-end lg:justify-between">
        <div className="flex flex-col gap-3">
          <h1 className="max-w-[16ch] font-display text-3xl font-semibold leading-tight text-ink sm:text-4xl lg:text-5xl">
            The garden asks{" "}
            <span className="font-mono italic text-accent-strong">
              five rites
            </span>{" "}
            of you today.
          </h1>
          {/* Italic epigraph uses muted ink (darkened for AA, D-008 #4). */}
          <p className="max-w-[40ch] font-mono text-lg italic text-ink-muted">
            Two waterings stand overdue; the orchid awaits its feeding.
          </p>
        </div>

        <ul className="flex divide-x divide-border self-start border-card border-border bg-surface-raised shadow-card">
          {STAT_PODS.map((pod) => (
            <li key={pod.label} className="px-5 py-3 text-center">
              <div
                className={`font-display text-2xl font-bold leading-none ${podToneClass(
                  pod.tone,
                )}`}
              >
                {pod.value}
              </div>
              <div className="mt-1.5 font-label text-xs font-semibold uppercase tracking-widest text-ink-muted">
                {pod.label}
              </div>
            </li>
          ))}
        </ul>
      </header>

      <div className="flex flex-col gap-4">
        <h2 className="flex items-center gap-3 font-label text-sm font-semibold uppercase tracking-widest text-ink">
          <span aria-hidden="true" className="h-px w-6 bg-accent" />
          Needs care
        </h2>
        <ul className="grid grid-cols-1 gap-4 sm:grid-cols-2 lg:grid-cols-3">
          {CARE_CARDS.map((card) => (
            <li
              key={card.name}
              className="flex flex-col border-card border-border bg-surface-raised shadow-card"
            >
              <div className="flex items-center justify-between border-b-control border-border px-4 py-2">
                <span className="font-label text-xs font-semibold uppercase tracking-widest text-ink-muted">
                  {card.room}
                </span>
                <span
                  className={`rounded-pill border-control px-2.5 py-1 font-label text-xs font-semibold uppercase tracking-widest ${statusClass(
                    card.status,
                  )}`}
                >
                  {card.task} · {card.status}
                </span>
              </div>
              <div className="flex flex-col gap-1 px-4 py-4">
                <h3 className="font-display text-xl font-semibold text-ink">
                  {card.name}
                </h3>
                <p className="font-mono text-base italic text-accent-2-strong">
                  {card.species}
                </p>
                <p className="mt-2 font-mono text-base italic text-ink-muted">
                  {card.when}
                </p>
              </div>
            </li>
          ))}
        </ul>
      </div>

      <HealthBadge />
    </section>
  );
}
