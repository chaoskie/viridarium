import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  createLocation,
  deleteLocation,
  fetchLocations,
  updateLocation,
  type Location,
  type LocationInput,
} from "@/lib/api/locations";

interface UseLocationsResult {
  readonly locations: readonly Location[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly reload: () => Promise<void>;
  readonly create: (input: LocationInput) => Promise<void>;
  readonly update: (id: number, input: LocationInput) => Promise<void>;
  readonly remove: (id: number) => Promise<void>;
}

/** Turn any thrown value (incl. `ApiError`) into a human-readable message. */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/**
 * Owns the Rooms list state: `locations`/`loading`/`error` plus
 * `reload`/`create`/`update`/`remove`. Loads on mount; each mutation calls the
 * API then reloads so the list reflects the server (design §3 [TEMPLATE]).
 */
export function useLocations(): UseLocationsResult {
  const [locations, setLocations] = useState<readonly Location[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const rooms = await fetchLocations();
      setLocations(rooms);
    } catch (err: unknown) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }, []);

  useEffect(() => {
    void reload();
  }, [reload]);

  const create = useCallback(
    async (input: LocationInput): Promise<void> => {
      await createLocation(input);
      await reload();
    },
    [reload],
  );

  const update = useCallback(
    async (id: number, input: LocationInput): Promise<void> => {
      await updateLocation(id, input);
      await reload();
    },
    [reload],
  );

  const remove = useCallback(
    async (id: number): Promise<void> => {
      await deleteLocation(id);
      await reload();
    },
    [reload],
  );

  return { locations, loading, error, reload, create, update, remove };
}
