import { useCallback, useEffect, useState } from "react";

import { ApiError } from "@/lib/api/client";
import {
  deletePhoto,
  fetchPhotos,
  setCoverPhoto,
  uploadPhoto,
  type Photo,
} from "@/lib/api/photos";

interface UsePhotosResult {
  readonly photos: readonly Photo[];
  readonly loading: boolean;
  readonly error: string | null;
  readonly reload: () => Promise<void>;
  readonly upload: (file: File) => Promise<void>;
  readonly setCover: (photoId: number) => Promise<void>;
  readonly remove: (photoId: number) => Promise<void>;
}

/**
 * Turn any thrown value (incl. `ApiError`) into a human-readable message. The
 * two security-bearing upload rejects get friendly, specific copy (design
 * `usePhotos.ts`): 415 -> unsupported type, 413 -> oversize.
 */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    if (err.status === 415) {
      return "Only JPEG, PNG, or WebP images are allowed.";
    }
    if (err.status === 413) {
      return "That image is too large (max 10 MB).";
    }
    return `Could not reach the server (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong. Please try again.";
}

/**
 * Owns one plant's photo gallery: `photos`/`loading`/`error` plus
 * `reload`/`upload`/`setCover`/`remove`. Loads on mount (and whenever
 * `plantId` changes); each mutation calls the API then reloads so the grid
 * reflects the server (mirrors `usePlants`, design §3 [TEMPLATE]).
 *
 * Unlike `usePlants`, mutations here TRAP errors into `error` so the gallery
 * modal can surface the friendly 415/413 copy without a separate form layer.
 */
export function usePhotos(plantId: number): UsePhotosResult {
  const [photos, setPhotos] = useState<readonly Photo[]>([]);
  const [loading, setLoading] = useState<boolean>(true);
  const [error, setError] = useState<string | null>(null);

  const reload = useCallback(async (): Promise<void> => {
    setLoading(true);
    setError(null);
    try {
      const rows = await fetchPhotos(plantId);
      setPhotos(rows);
    } catch (err: unknown) {
      setError(toMessage(err));
    } finally {
      setLoading(false);
    }
  }, [plantId]);

  useEffect(() => {
    void reload();
  }, [reload]);

  const upload = useCallback(
    async (file: File): Promise<void> => {
      setError(null);
      try {
        await uploadPhoto(plantId, file);
      } catch (err: unknown) {
        setError(toMessage(err));
        return;
      }
      await reload();
    },
    [plantId, reload],
  );

  const setCover = useCallback(
    async (photoId: number): Promise<void> => {
      setError(null);
      try {
        await setCoverPhoto(plantId, photoId);
      } catch (err: unknown) {
        setError(toMessage(err));
        return;
      }
      await reload();
    },
    [plantId, reload],
  );

  const remove = useCallback(
    async (photoId: number): Promise<void> => {
      setError(null);
      try {
        await deletePhoto(plantId, photoId);
      } catch (err: unknown) {
        setError(toMessage(err));
        return;
      }
      await reload();
    },
    [plantId, reload],
  );

  return { photos, loading, error, reload, upload, setCover, remove };
}
