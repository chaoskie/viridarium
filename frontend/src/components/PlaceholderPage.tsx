import type { ReactNode } from "react";

interface PlaceholderPageProps {
  readonly title: string;
}

/** Stub page for nav destinations not yet built (Plants, Rooms, Journal, Settings). */
export function PlaceholderPage({ title }: PlaceholderPageProps): ReactNode {
  return (
    <section className="flex flex-col gap-3">
      <h1 className="font-display text-4xl font-extrabold text-ink">{title}</h1>
      <p className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card">
        This page is not built yet.
      </p>
    </section>
  );
}
