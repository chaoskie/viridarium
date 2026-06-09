import { useCallback, useEffect, useRef, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  archivePlant,
  createPlant,
  deletePlant,
  fetchPlants,
  unarchivePlant,
  updatePlant,
  type Plant,
  type PlantFilter,
  type PlantInput,
} from "@/lib/api/plants";

interface UsePlantsResult {
  readonly plants: readonly Plant[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly reload: (filter?: PlantFilter) => Promise<void>;
  readonly create: (input: PlantInput) => Promise<void>;
  readonly update: (id: number, input: PlantInput) => Promise<void>;
  readonly remove: (id: number) => Promise<void>;
  readonly archive: (id: number) => Promise<void>;
  readonly unarchive: (id: number) => Promise<void>;
}

/** Turn any thrown value (incl. `ApiError`) into a human-readable message. */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/**
 * Owns the Plants list state: `plants`/`loading`/`error` plus
 * `reload(filter)`/`create`/`update`/`remove`. Loads on mount; `reload` re-fetches
 * server-side with the given search/filter (D4); each mutation calls the API then
 * reloads so the list reflects the server (design §3 [TEMPLATE]).
 *
 * Mutations let `ApiError` (incl. 422) propagate so the form can surface a
 * field-level message; only the load path traps errors into `error`.
 */
export function usePlants(): UsePlantsResult {
  const [plants, setPlants] = useState<readonly Plant[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  // The last filter passed to `reload`, so archive/unarchive can re-fetch the
  // SAME view (active/archived/all). Without this a row crossing the boundary
  // would incoherently vanish/reappear (design §3, US-2.4).
  const lastFilterRef = useRef<PlantFilter | undefined>(undefined);

  const reload = useCallback(async (filter?: PlantFilter): Promise<void> => {
    lastFilterRef.current = filter;
    setLoading(true);
    setError(null);
    try {
      const rows = await fetchPlants(filter);
      setPlants(rows);
    } catch (err: unknown) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  // All mutations reload the SAME view that is currently shown (lastFilterRef),
  // so create/edit/delete/archive don't silently snap the list back to the
  // default Active view while the filter controls still read otherwise.
  const create = useCallback(
    async (input: PlantInput): Promise<void> => {
      await createPlant(input);
      await reload(lastFilterRef.current);
    },
    [reload],
  );

  const update = useCallback(
    async (id: number, input: PlantInput): Promise<void> => {
      await updatePlant(id, input);
      await reload(lastFilterRef.current);
    },
    [reload],
  );

  const remove = useCallback(
    async (id: number): Promise<void> => {
      await deletePlant(id);
      await reload(lastFilterRef.current);
    },
    [reload],
  );

  const archive = useCallback(
    async (id: number): Promise<void> => {
      await archivePlant(id);
      await reload(lastFilterRef.current);
    },
    [reload],
  );

  const unarchive = useCallback(
    async (id: number): Promise<void> => {
      await unarchivePlant(id);
      await reload(lastFilterRef.current);
    },
    [reload],
  );

  return {
    plants,
    loading,
    error,
    reload,
    create,
    update,
    remove,
    archive,
    unarchive,
  };
}
