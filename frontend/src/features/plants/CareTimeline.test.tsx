import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { TimelineEntry } from "@/lib/api/timeline";

import { CareTimeline } from "./CareTimeline";

// One event of each of the four types, an observe with health + inline photo,
// and a standalone kind:photo entry - the full discriminated shape (F-2 mirror).
const SAMPLE_TIMELINE: TimelineEntry[] = [
  {
    kind: "photo",
    date: "2026-06-15",
    photo: { id: 11, url: "/api/v1/plants/1/photos/11" },
  },
  {
    kind: "event",
    date: "2026-06-14",
    event_type: "observe",
    note: "New leaf unfurling",
    health: "good",
    photo: { id: 12, url: "/api/v1/plants/1/photos/12" },
  },
  {
    kind: "event",
    date: "2026-06-13",
    event_type: "repot",
    note: null,
    health: null,
    photo: null,
  },
  {
    kind: "event",
    date: "2026-06-12",
    event_type: "feed",
    note: null,
    health: null,
    photo: null,
  },
  {
    kind: "event",
    date: "2026-06-11",
    event_type: "water",
    note: null,
    health: null,
    photo: null,
  },
];

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

function fail(status: number): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

function stubFetch(response: Response): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("CareTimeline", () => {
  it("renders each of the four event types with a distinct marker (F-4)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));
    render(<CareTimeline plantId={1} />);

    // Each event type carries a per-type test-id marker; the four are distinct.
    await waitFor(() => {
      expect(screen.getByTestId("event-marker-water")).toBeInTheDocument();
    });
    const markers = [
      screen.getByTestId("event-marker-water"),
      screen.getByTestId("event-marker-feed"),
      screen.getByTestId("event-marker-repot"),
      screen.getByTestId("event-marker-observe"),
    ];
    const labels = markers.map((el) => el.textContent?.trim());
    // No two types share the same rendered marker label.
    expect(new Set(labels).size).toBe(4);
  });

  it("shows the health rating and renders an event photo inline (F-5)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));
    render(<CareTimeline plantId={1} />);

    const observeMarker = await screen.findByTestId("event-marker-observe");
    const entry = observeMarker.closest("li");
    expect(entry).not.toBeNull();
    const scope = within(entry as HTMLElement);

    // Health rating is visible on the observe entry.
    expect(scope.getByText(/good/i)).toBeInTheDocument();
    // The inline photo renders with the contracted url, uncropped like the
    // standalone entry (both share TimelinePhotoImage - BUG-009).
    const inlinePhoto = scope.getByRole("img");
    expect(inlinePhoto).toHaveAttribute("src", "/api/v1/plants/1/photos/12");
    expect(inlinePhoto).toHaveClass("object-contain");

    // A water entry (photo:null, health:null) carries no image and no health chip.
    const waterEntry = screen
      .getByTestId("event-marker-water")
      .closest("li") as HTMLElement;
    expect(within(waterEntry).queryByRole("img")).not.toBeInTheDocument();
  });

  it("renders a standalone kind:photo entry as a photo (F-6)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));
    render(<CareTimeline plantId={1} />);

    const photoEntry = await screen.findByTestId("photo-entry");
    const scope = within(photoEntry);
    expect(scope.getByRole("img")).toHaveAttribute(
      "src",
      "/api/v1/plants/1/photos/11",
    );
    // It is a photo entry, not mislabelled as an event (no event-type marker).
    expect(scope.queryByTestId(/event-marker-/)).not.toBeInTheDocument();
  });

  it("renders timeline photos uncropped so portrait images are not cut off (BUG-009)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));
    render(<CareTimeline plantId={1} />);

    const photoEntry = await screen.findByTestId("photo-entry");
    const img = within(photoEntry).getByRole("img");
    // The whole image must be shown (contained), never cropped to fill the box.
    expect(img).toHaveClass("object-contain");
    expect(img).not.toHaveClass("object-cover");
  });

  it("renders an empty state for no history (F-7)", async () => {
    stubFetch(okJson(200, []));
    render(<CareTimeline plantId={1} />);

    await waitFor(() => {
      expect(screen.getByText(/no history yet/i)).toBeInTheDocument();
    });
    // No perpetual spinner, no crash.
    expect(screen.queryByText(/loading/i)).not.toBeInTheDocument();
  });

  it("preserves the server's newest-first order in the render (F-8)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));
    render(<CareTimeline plantId={1} />);

    await screen.findByTestId("photo-entry");
    const items = screen.getAllByRole("listitem");
    // DOM order matches the array order: photo(15), observe(14), repot(13),
    // feed(12), water(11) - the FE does not re-sort (AC1).
    expect(items).toHaveLength(5);
    expect(items[0]).toHaveTextContent(/2026-06-15/);
    expect(items[1]).toHaveTextContent(/2026-06-14/);
    expect(items[4]).toHaveTextContent(/2026-06-11/);
  });

  it("surfaces a load error inline without crashing (F-9)", async () => {
    stubFetch(fail(500));
    render(<CareTimeline plantId={1} />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });
});
