import type { ReactNode } from "react";

interface PlaceholderPageProps {
  readonly title: string;
}

/** Stub page for nav destinations not yet built (Plants, Rooms, Journal, Settings). */
export function PlaceholderPage({ title }: PlaceholderPageProps): ReactNode {
  return (
    <section className="flex flex-col gap-2">
      <h1 className="font-display text-2xl font-semibold">{title}</h1>
      <p className="text-ink-muted">This page is not built yet.</p>
    </section>
  );
}
