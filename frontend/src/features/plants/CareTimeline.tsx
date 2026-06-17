import { useEffect, useState } from "react";
import type { ReactNode } from "react";

import type { CareEventType } from "@/lib/api/careEvents";
import { ApiError } from "@/lib/api/client";
import {
  getTimeline,
  type TimelineEntry,
  type TimelineEvent,
  type TimelinePhoto,
} from "@/lib/api/timeline";

/**
 * A distinct marker per event type (FE-011: distinguishable by label + glyph,
 * NOT colour alone). Each type has its own glyph and its own human label, so
 * the four read differently for a sighted user and a screen-reader user alike.
 */
const EVENT_MARKER: Record<CareEventType, { glyph: string; label: string }> = {
  water: { glyph: "💧", label: "Watered" },
  feed: { glyph: "🌱", label: "Fed" },
  repot: { glyph: "🪴", label: "Repotted" },
  observe: { glyph: "👁", label: "Observed" },
};

/** A human label for an observe health rating (good / fair / bad). */
const HEALTH_LABEL: Record<string, string> = {
  good: "Good",
  fair: "Fair",
  bad: "Bad",
};

type LoadState =
  | { readonly kind: "loading" }
  | { readonly kind: "ready"; readonly entries: readonly TimelineEntry[] }
  | { readonly kind: "error"; readonly message: string };

/** Turn any thrown value (incl. `ApiError`) into a human-readable message. */
function toMessage(err: unknown): string {
  if (err instanceof ApiError) {
    return `Could not load this plant's history (error ${String(err.status)}). Please try again.`;
  }
  return "Something went wrong loading the history. Please try again.";
}

const CARD_CLASSES =
  "flex flex-col gap-2 rounded-card border-card border-border bg-surface-raised p-4 shadow-card";

const CHIP_CLASSES =
  "inline-flex items-center gap-1.5 rounded-pill border-control border-border bg-surface px-2 py-0.5 font-label text-xs font-semibold uppercase tracking-widest text-ink-muted";

/** The inline / standalone photo image, rendered from the server-provided url. */
function TimelinePhotoImage({
  url,
  alt,
}: {
  readonly url: string;
  readonly alt: string;
}): ReactNode {
  return (
    <img
      src={url}
      alt={alt}
      loading="lazy"
      // object-contain (not -cover): the timeline is a history feed, so the
      // whole photo must show within the height cap - a portrait image is
      // letterboxed, never cropped to a wide band (BUG-009).
      className="mt-1 max-h-64 w-full rounded-control border-control border-border object-contain"
    />
  );
}

/** One care-event entry: a per-type marker, date, optional note/health/photo. */
function EventEntry({ entry }: { readonly entry: TimelineEvent }): ReactNode {
  const marker = EVENT_MARKER[entry.event_type];
  return (
    <li className={CARD_CLASSES}>
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span
          className={CHIP_CLASSES}
          data-testid={`event-marker-${entry.event_type}`}
        >
          <span aria-hidden="true">{marker.glyph}</span>
          {marker.label}
        </span>
        <time className="font-mono text-sm text-ink-muted">{entry.date}</time>
      </div>
      {entry.health !== null ? (
        <p className="font-body text-sm text-ink">
          Health:{" "}
          <span className="font-semibold">
            {HEALTH_LABEL[entry.health] ?? entry.health}
          </span>
        </p>
      ) : null}
      {entry.note !== null && entry.note.length > 0 ? (
        <p className="font-body text-base text-ink">{entry.note}</p>
      ) : null}
      {entry.photo !== null ? (
        <TimelinePhotoImage
          url={entry.photo.url}
          alt={`Photo from the ${marker.label.toLowerCase()} entry on ${entry.date}`}
        />
      ) : null}
    </li>
  );
}

/** One standalone photo entry: the image with its date. */
function PhotoEntry({ entry }: { readonly entry: TimelinePhoto }): ReactNode {
  return (
    <li className={CARD_CLASSES} data-testid="photo-entry">
      <div className="flex flex-wrap items-center justify-between gap-2">
        <span className={CHIP_CLASSES}>
          <span aria-hidden="true">📷</span>
          Photo
        </span>
        <time className="font-mono text-sm text-ink-muted">{entry.date}</time>
      </div>
      <TimelinePhotoImage
        url={entry.photo.url}
        alt={`Photo from ${entry.date}`}
      />
    </li>
  );
}

/**
 * The per-plant care history feed (US-3.4). Loads `GET .../{id}/timeline` on
 * mount and renders the merged event + photo entries newest-first, exactly in
 * the server's order (the FE never re-sorts; it trusts the contract, AC1).
 * Each event type shows a distinct marker (FE-011, not colour-only); observe
 * entries show their health rating; event and standalone photos render their
 * image inline. A plant with no history shows an empty state; a failed load
 * degrades to an inline error (no crash).
 */
export function CareTimeline({
  plantId,
}: {
  readonly plantId: number;
}): ReactNode {
  const [state, setState] = useState<LoadState>({ kind: "loading" });

  useEffect(() => {
    let active = true;
    setState({ kind: "loading" });
    void getTimeline(plantId)
      .then((entries) => {
        if (active) {
          setState({ kind: "ready", entries });
        }
      })
      .catch((err: unknown) => {
        if (active) {
          setState({ kind: "error", message: toMessage(err) });
        }
      });
    return () => {
      active = false;
    };
  }, [plantId]);

  if (state.kind === "loading") {
    return (
      <p
        className="rounded-card border-card border-border bg-surface-raised p-5 font-label text-sm uppercase tracking-wide text-ink-muted shadow-card"
        aria-live="polite"
      >
        Loading history...
      </p>
    );
  }

  if (state.kind === "error") {
    return (
      <p
        className="rounded-card border-card border-danger bg-surface-raised p-5 font-body text-base text-danger shadow-card"
        role="alert"
      >
        {state.message}
      </p>
    );
  }

  if (state.entries.length === 0) {
    return (
      <p className="rounded-card border-card border-border bg-surface-raised p-5 font-body text-base text-ink-muted shadow-card">
        No history yet. Log a care event or add a photo to start this plant's
        timeline.
      </p>
    );
  }

  return (
    <ul className="flex flex-col gap-3">
      {state.entries.map((entry, index) =>
        entry.kind === "event" ? (
          <EventEntry key={`event-${String(index)}`} entry={entry} />
        ) : (
          <PhotoEntry key={`photo-${String(index)}`} entry={entry} />
        ),
      )}
    </ul>
  );
}
