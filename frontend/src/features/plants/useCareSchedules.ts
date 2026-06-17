import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  deleteSchedule,
  fetchSchedules,
  upsertSchedule,
  type CareSchedule,
  type CareScheduleInput,
  type CareType,
} from "@/lib/api/careSchedules";

interface UseCareSchedulesResult {
  readonly schedules: readonly CareSchedule[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly reload: () => Promise<void>;
  readonly upsert: (
    careType: CareType,
    input: CareScheduleInput,
  ) => Promise<void>;
  readonly remove: (careType: CareType) => Promise<void>;
}

/**
 * Turn any thrown value (incl. `ApiError`) into a human-readable message. A 422
 * is the validation reject for an out-of-range interval / bad enum; everything
 * else degrades to a generic retry message (mirrors `usePhotos.toMessage`).
 */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 422) {
      return "Those values are out of range. Use whole days between 1 and 3650.";
    }
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/**
 * Owns one plant's care schedules: `schedules`/`loading`/`error` plus
 * `reload`/`upsert`/`remove`. Loads on mount (and whenever `plantId` changes);
 * each mutation calls the API then reloads so the list reflects the server
 * (mirrors `usePhotos`, design §frontend). Mutations TRAP errors into `error`
 * so the modal can surface friendly copy without a separate form layer.
 *
 * `loading` reflects the INITIAL load only - it is armed by the `useState`
 * initializer and never re-set by a mutation's refetch. Re-arming it on every
 * `upsert`/`remove` would make the modal swap the whole section list for a
 * placeholder mid-edit, unmounting the sibling section and discarding its
 * unsaved local form state (BUG-007). The post-mutation refetch is silent;
 * the saved section still re-keys on its new `updated_at`.
 */
export function useCareSchedules(plantId: number): UseCareSchedulesResult {
  const [schedules, setSchedules] = useState<readonly CareSchedule[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (): Promise<void> => {
    setError(null);
    try {
      const rows = await fetchSchedules(plantId);
      setSchedules(rows);
    } catch (err: unknown) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }, [plantId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const upsert = useCallback(
    async (careType: CareType, input: CareScheduleInput): Promise<void> => {
      setError(null);
      try {
        await upsertSchedule(plantId, careType, input);
      } catch (err: unknown) {
        setError(toMessage(err));
        return;
      }
      await reload();
    },
    [plantId, reload],
  );

  const remove = useCallback(
    async (careType: CareType): Promise<void> => {
      setError(null);
      try {
        await deleteSchedule(plantId, careType);
      } catch (err: unknown) {
        setError(toMessage(err));
        return;
      }
      await reload();
    },
    [plantId, reload],
  );

  return { schedules, loading, error, reload, upsert, remove };
}
