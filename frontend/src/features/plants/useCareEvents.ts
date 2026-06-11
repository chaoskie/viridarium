import { useCallback, useState } from "react";

import {
  createEvent,
  type CareEvent,
  type CareEventInput,
} from "@/lib/api/careEvents";
import { ApiError } from "@/lib/api/client";

interface UseCareEventsResult {
  readonly error: string | null;
  /** Append one event; traps failures into `error` and resolves null. */
  readonly log: (input: CareEventInput) => Promise<CareEvent | null>;
}

/**
 * Turn any thrown value (incl. `ApiError`) into a human-readable message. A
 * 422 is the validation reject (future date, health on a non-observe type);
 * everything else degrades to a generic retry message (mirrors
 * `useCareSchedules.toMessage`).
 */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 422) {
      return "The server rejected this entry. Check the date and fields.";
    }
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/**
 * Owns logging care events for one plant (US-3.2): `log` POSTs the event and
 * TRAPS errors into `error` so the quick actions and the log modal can surface
 * friendly copy inline (mirrors the `useCareSchedules` mutation pattern). No
 * list state - the timeline view is US-3.4, not this story.
 */
export function useCareEvents(plantId: number): UseCareEventsResult {
  const [error, setError] = useState<string | null>(null);

  const log = useCallback(
    async (input: CareEventInput): Promise<CareEvent | null> => {
      setError(null);
      try {
        return await createEvent(plantId, input);
      } catch (err: unknown) {
        setError(toMessage(err));
        return null;
      }
    },
    [plantId],
  );

  return { error, log };
}
