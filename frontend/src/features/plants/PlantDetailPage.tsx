import { useEffect, useState } from "react";
import type { ReactNode } from "react";
import { Link, useParams } from "react-router-dom";

import { fetchPlant, type Plant } from "@/lib/api/plants";

import { CareTimeline } from "./CareTimeline";

type PlantState =
  | { readonly kind: "loading" }
  | { readonly kind: "ready"; readonly plant: Plant }
  | { readonly kind: "error" };

const BACK_LINK_CLASSES =
  "inline-flex min-h-tap-min items-center gap-1.5 font-label text-xs font-semibold uppercase tracking-widest text-ink-muted hover:text-ink";

/**
 * Minimal plant detail page (US-3.4) - a US-4.3 precursor. A thin header (the
 * plant name + a back link to the list) hosting the `<CareTimeline>` feed for
 * the routed plant id. Deliberately does NOT build attributes / schedules /
 * next-due / a gallery (those are US-4.3, out of scope here). An invalid or
 * absent id degrades to a heading placeholder; the timeline's own empty/error
 * state covers the data side.
 */
export function PlantDetailPage(): ReactNode {
  const params = useParams<{ id: string }>();
  const plantId = Number(params.id);
  const validId = Number.isInteger(plantId) && plantId > 0;

  const [state, setState] = useState<PlantState>({ kind: "loading" });

  useEffect(() => {
    if (!validId) {
      setState({ kind: "error" });
      return;
    }
    let active = true;
    setState({ kind: "loading" });
    void fetchPlant(plantId)
      .then((plant) => {
        if (active) {
          setState({ kind: "ready", plant });
        }
      })
      .catch(() => {
        if (active) {
          // The name degrades gracefully; the timeline still renders / errors.
          setState({ kind: "error" });
        }
      });
    return () => {
      active = false;
    };
  }, [plantId, validId]);

  const heading = state.kind === "ready" ? state.plant.name : "Plant";

  return (
    <section className="flex flex-col gap-6">
      <header className="flex flex-col gap-3">
        <Link to="/plants" className={BACK_LINK_CLASSES}>
          <span aria-hidden="true">←</span>
          Back to plants
        </Link>
        <h1 className="font-display text-4xl font-extrabold text-ink break-words">
          {heading}
        </h1>
      </header>

      {validId ? (
        <CareTimeline plantId={plantId} />
      ) : (
        <p
          className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-ink-muted shadow-card"
          role="alert"
        >
          That plant could not be found.
        </p>
      )}
    </section>
  );
}
