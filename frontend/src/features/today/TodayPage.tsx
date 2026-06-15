import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import { todayIsoDate } from "@/lib/api/careEvents";
import { fetchLocations, type Location } from "@/lib/api/locations";
import { fetchPlants, type Plant } from "@/lib/api/plants";

import { buildTodayGroups } from "./buildTodayGroups";
import { TodayCard } from "./TodayCard";

type LoadState =
  | { readonly kind: "loading" }
  | { readonly kind: "error" }
  | {
      readonly kind: "ready";
      readonly plants: readonly Plant[];
      readonly locations: readonly Location[];
    };

/**
 * The Today view (US-4.1): the v0.1 payoff screen. Loads plants + locations,
 * derives the plants needing water or feed today via the pure
 * `buildTodayGroups`, and renders them grouped by location with one-tap
 * Water/Feed/Both actions per card. A satisfied care type drops in place and a
 * card leaves the list once nothing is due, without a full reload. An empty
 * state celebrates "nothing due"; loading and load-error states degrade
 * gracefully.
 */
export function TodayPage(): ReactNode {
  const [state, setState] = useState<LoadState>({ kind: "loading" });
  // Plants whose every due care type has been logged this session - dropped
  // from the derived list so the card leaves without a full reload (AC3).
  const [clearedPlantIds, setClearedPlantIds] = useState<readonly number[]>([]);

  useEffect(() => {
    let active = true;

    Promise.all([fetchPlants(), fetchLocations()])
      .then(([plants, locations]) => {
        if (active) {
          setState({ kind: "ready", plants, locations });
        }
      })
      .catch(() => {
        if (active) {
          setState({ kind: "error" });
        }
      });

    return () => {
      active = false;
    };
  }, []);

  if (state.kind === "loading") {
    return (
      <section className="flex flex-col gap-8" aria-busy="true">
        <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">
          Today
        </h1>
        <p className="font-mono text-lg italic text-ink-muted">Loading...</p>
      </section>
    );
  }

  if (state.kind === "error") {
    return (
      <section className="flex flex-col gap-8">
        <h1 className="font-display text-3xl font-semibold text-ink sm:text-4xl">
          Today
        </h1>
        <p
          role="alert"
          className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-danger shadow-card"
        >
          Could not load your plants. Please try again.
        </p>
      </section>
    );
  }

  const visiblePlants = state.plants.filter(
    (p) => !clearedPlantIds.includes(p.id),
  );
  const groups = buildTodayGroups(
    visiblePlants,
    state.locations,
    todayIsoDate(),
  );

  return (
    <section className="flex flex-col gap-8">
      <header className="flex flex-col gap-3">
        <h1 className="max-w-[16ch] font-display text-3xl font-semibold leading-tight text-ink sm:text-4xl">
          Today
        </h1>
        <p className="max-w-[40ch] font-mono text-lg italic text-ink-muted">
          What needs water or feed today.
        </p>
      </header>

      {groups.length === 0 ? (
        <div className="rounded-card border-card border-border bg-surface-raised p-8 text-center shadow-card">
          <p className="font-display text-2xl font-semibold text-ink">
            Nothing due - enjoy the view
          </p>
          <p className="mt-2 font-mono text-base italic text-ink-muted">
            Every plant is watered and fed. Come back tomorrow.
          </p>
        </div>
      ) : (
        <div className="flex flex-col gap-8">
          {groups.map((group) => (
            <section key={group.locationName} className="flex flex-col gap-4">
              <h2 className="flex items-center gap-3 font-label text-sm font-semibold uppercase tracking-widest text-ink">
                <span aria-hidden="true" className="h-px w-6 bg-accent" />
                {group.locationName}
              </h2>
              <ul className="flex flex-col gap-3">
                {group.cards.map((card) => (
                  <TodayCard
                    key={card.plant.id}
                    card={card}
                    onAllCareLogged={(plantId) => {
                      setClearedPlantIds((prev) => [...prev, plantId]);
                    }}
                  />
                ))}
              </ul>
            </section>
          ))}
        </div>
      )}
    </section>
  );
}
