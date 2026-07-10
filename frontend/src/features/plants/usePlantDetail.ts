import { useCallback, useEffect, useRef, useState } from "react";

import { fetchPlant, type Plant } from "@/lib/api/plants";

export type PlantDetailState =
  | { readonly kind: "loading" }
  | { readonly kind: "ready"; readonly plant: Plant }
  | { readonly kind: "error" };

interface UsePlantDetailResult {
  readonly state: PlantDetailState;
  /** Refetch the plant (the every-mutation callback, design §data-flow). */
  readonly reload: () => Promise<void>;
}

/**
 * Owns one plant's detail state machine (`loading | ready | error`) plus a
 * `reload()` used as the after-mutation callback so schedules/next-due/cover
 * stay fresh (US-4.3, mirrors the `usePlants` reload pattern). An invalid or
 * non-positive id errors immediately without a network call.
 */
export function usePlantDetail(plantId: number): UsePlantDetailResult {
  const validId = Number.isInteger(plantId) && plantId > 0;
  const [state, setState] = useState<PlantDetailState>(
    validId ? { kind: "loading" } : { kind: "error" },
  );

  // Staleness guard: a slow fetch for a previous plant id (or an older
  // overlapping reload) must never overwrite the latest request's state.
  const generation = useRef(0);

  const reload = useCallback(async (): Promise<void> => {
    const requested = ++generation.current;
    if (!validId) {
      setState({ kind: "error" });
      return;
    }
    try {
      const plant = await fetchPlant(plantId);
      if (generation.current === requested) {
        setState({ kind: "ready", plant });
      }
    } catch {
      if (generation.current === requested) {
        setState({ kind: "error" });
      }
    }
  }, [plantId, validId]);

  useEffect(() => {
    if (!validId) {
      setState({ kind: "error" });
      return;
    }
    setState({ kind: "loading" });
    void reload();
  }, [reload, validId]);

  return { state, reload };
}
