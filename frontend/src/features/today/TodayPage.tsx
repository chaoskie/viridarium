import type { ReactNode } from "react";

import { HealthBadge } from "./HealthBadge";

export function TodayPage(): ReactNode {
  return (
    <section className="flex flex-col gap-4">
      <header>
        <h1 className="font-display text-2xl font-semibold">Today</h1>
        <p className="text-ink-muted">
          What needs care today will appear here once plants exist.
        </p>
      </header>
      <HealthBadge />
    </section>
  );
}
