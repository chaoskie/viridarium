import { render, screen, waitFor, within } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Location } from "@/lib/api/locations";
import type { Plant, ScheduleDue } from "@/lib/api/plants";

import { TodayPage } from "./TodayPage";

/** Today's local calendar date as YYYY-MM-DD (independent oracle). */
function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

/** A date `offsetDays` from local today (negative = past). */
function dateOffset(offsetDays: number): string {
  const now = new Date();
  now.setDate(now.getDate() + offsetDays);
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

function _schedule(
  care_type: "water" | "feed",
  next_due: string | null,
  overdue_days: number | null,
): ScheduleDue {
  return { care_type, next_due, overdue_days };
}

function _plant(
  id: number,
  name: string,
  location_id: number | null,
  schedules: readonly ScheduleDue[],
): Plant {
  return {
    id,
    name,
    species: null,
    location_id,
    acquired_on: null,
    pot_size_cm: null,
    pot_material: null,
    light_level: null,
    notes: null,
    tags: [],
    archived: false,
    cover_photo_id: null,
    schedules,
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  };
}

const SAMPLE_LOCATIONS: Location[] = [
  {
    id: 1,
    name: "Bath",
    notes: null,
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  },
  {
    id: 2,
    name: "Kitchen",
    notes: null,
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  },
];

const SAMPLE_PLANTS: Plant[] = [
  // overdue 3 days on water, in Kitchen
  _plant(1, "Monstera", 2, [_schedule("water", dateOffset(-3), 3)]),
  // overdue 1 day on water, in Bath (singular copy)
  _plant(2, "Fig", 1, [_schedule("water", dateOffset(-1), 1)]),
  // due-today on feed, in Kitchen
  _plant(3, "Orchid", 2, [_schedule("feed", localToday(), 0)]),
  // both-due (water overdue 2 + feed due today), homeless
  _plant(4, "Pothos", null, [
    _schedule("water", dateOffset(-2), 2),
    _schedule("feed", localToday(), 0),
  ]),
  // not-due (future water + paused feed), in Kitchen - must be absent
  _plant(5, "Cactus", 2, [
    _schedule("water", dateOffset(5), 0),
    _schedule("feed", null, null),
  ]),
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

/** Route GET by path: /plants -> plants, /locations -> locations. */
function stubRoutes(
  plants: Plant[],
  locations: Location[],
): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn((input: string) => {
    if (input.includes("/locations")) {
      return Promise.resolve(okJson(200, locations));
    }
    return Promise.resolve(okJson(200, plants));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("TodayPage", () => {
  it("C-1 renders groups with location headers; not-due plant absent", async () => {
    stubRoutes(SAMPLE_PLANTS, SAMPLE_LOCATIONS);
    render(<TodayPage />);

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /^Bath$/i }),
      ).toBeInTheDocument();
    });
    expect(
      screen.getByRole("heading", { name: /^Kitchen$/i }),
    ).toBeInTheDocument();
    expect(
      screen.getByRole("heading", { name: /no location/i }),
    ).toBeInTheDocument();
    // not-due plant is filtered out of the render entirely
    expect(screen.queryByText("Cactus")).not.toBeInTheDocument();
    // due plants present
    expect(screen.getByText("Monstera")).toBeInTheDocument();
    expect(screen.getByText("Pothos")).toBeInTheDocument();
  });

  it("C-2 overdue entry: distinct marker + 'N days overdue' matching overdue_days", async () => {
    stubRoutes(SAMPLE_PLANTS, SAMPLE_LOCATIONS);
    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByText("Monstera")).toBeInTheDocument();
    });
    // Monstera is 3 days overdue; Fig is 1 day (singular).
    expect(screen.getByText(/3 days overdue/i)).toBeInTheDocument();
    expect(screen.getByText(/\b1 day overdue\b/i)).toBeInTheDocument();
  });

  it("C-3 due-today entry shows a neutral 'due today' badge", async () => {
    stubRoutes(SAMPLE_PLANTS, SAMPLE_LOCATIONS);
    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByText("Orchid")).toBeInTheDocument();
    });
    expect(screen.getAllByText(/due today/i).length).toBeGreaterThan(0);
  });

  it("C-4 empty-state renders when nothing is due", async () => {
    stubRoutes(
      [_plant(9, "Future", 1, [_schedule("water", dateOffset(4), 0)])],
      SAMPLE_LOCATIONS,
    );
    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByText(/nothing due/i)).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("heading", { name: /^Kitchen$/i }),
    ).not.toBeInTheDocument();
  });

  it("C-5 loading state then content", () => {
    const pending = new Promise<Response>(() => {
      /* never resolves */
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(() => pending),
    );
    render(<TodayPage />);
    expect(screen.getByText(/loading|checking/i)).toBeInTheDocument();
    expect(screen.queryByText(/nothing due/i)).not.toBeInTheDocument();
  });

  it("C-6 load error degrades gracefully (no crash)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn(() => Promise.resolve(fail(500))),
    );
    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
  });

  it("C-7 render order matches buildTodayGroups (page does not re-sort)", async () => {
    stubRoutes(SAMPLE_PLANTS, SAMPLE_LOCATIONS);
    render(<TodayPage />);

    await waitFor(() => {
      expect(screen.getByText("Monstera")).toBeInTheDocument();
    });
    const headings = screen
      .getAllByRole("heading", { level: 2 })
      .map((h) => h.textContent?.trim());
    // Named groups name-asc (Bath, Kitchen) then homeless last.
    const bathIdx = headings.indexOf("Bath");
    const kitchenIdx = headings.indexOf("Kitchen");
    const homelessIdx = headings.findIndex((t) => /no location/i.test(t ?? ""));
    expect(bathIdx).toBeGreaterThanOrEqual(0);
    expect(bathIdx).toBeLessThan(kitchenIdx);
    expect(kitchenIdx).toBeLessThan(homelessIdx);

    // Within Kitchen: Monstera (worstOverdue 3) before Orchid (0).
    const kitchenHeading = screen.getByRole("heading", { name: /^Kitchen$/i });
    const kitchenSection = kitchenHeading.closest("section");
    expect(kitchenSection).not.toBeNull();
    const section = within(kitchenSection as HTMLElement);
    const monstera = section.getByText("Monstera");
    const orchid = section.getByText("Orchid");
    expect(
      monstera.compareDocumentPosition(orchid) &
        Node.DOCUMENT_POSITION_FOLLOWING,
    ).toBeTruthy();
  });
});
