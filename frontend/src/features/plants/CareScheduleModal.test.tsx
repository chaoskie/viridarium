import {
  fireEvent,
  render,
  screen,
  waitFor,
  within,
} from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { CareScheduleModal } from "./CareScheduleModal";

const PLANT: Plant = {
  id: 1,
  name: "Fern",
  species: null,
  location_id: null,
  acquired_on: null,
  pot_size_cm: null,
  pot_material: null,
  outer_pot_material: null,
  outer_pot_size_cm: null,
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

function okJson(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response;
}

/** The water section's region, located by its accessible name. */
function waterSection(): HTMLElement {
  return screen.getByRole("group", { name: /water/i });
}

/** The feed section's region, located by its accessible name. */
function feedSection(): HTMLElement {
  return screen.getByRole("group", { name: /feed/i });
}

async function renderWithEmptyList(): Promise<void> {
  // Empty list on mount: water defaults to winter_interval dormancy with no
  // winter interval days, so the hint condition is met.
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson([])));
  render(<CareScheduleModal plant={PLANT} onClose={() => undefined} />);
  await waitFor(() => {
    expect(screen.queryByText(/loading schedules/i)).not.toBeInTheDocument();
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("CareScheduleModal no-winter-interval hint", () => {
  it("shows a non-blocking hint when dormancy is winter_interval and the winter interval is empty", async () => {
    await renderWithEmptyList();

    const water = waterSection();
    const hint = within(water).getByRole("note");
    expect(hint).toBeVisible();

    // The hint is non-blocking: with a valid interval entered the Save control
    // is enabled even while the hint is showing (the hint never gates saving).
    const intervalInput = within(water).getByLabelText(/^interval \(days\)/i);
    fireEvent.change(intervalInput, { target: { value: "7" } });

    expect(within(water).getByRole("note")).toBeVisible();
    expect(
      within(water).getByRole("button", { name: /save the water schedule/i }),
    ).toBeEnabled();
  });

  it("hides the hint when a winter interval is entered", async () => {
    await renderWithEmptyList();

    const water = waterSection();
    expect(within(water).queryByRole("note")).toBeInTheDocument();

    const winterInput = within(water).getByLabelText(/^winter interval/i);
    fireEvent.change(winterInput, { target: { value: "21" } });

    expect(within(water).queryByRole("note")).not.toBeInTheDocument();
  });

  it("dismisses the hint when its close control is clicked", async () => {
    await renderWithEmptyList();

    const water = waterSection();
    const dismiss = within(water).getByRole("button", {
      name: /dismiss the winter interval hint/i,
    });
    fireEvent.click(dismiss);

    expect(within(water).queryByRole("note")).not.toBeInTheDocument();
  });
});

describe("CareScheduleModal preserves unsaved sibling state (BUG-007)", () => {
  /**
   * Route fetch by method: the PUT upsert returns the saved feed schedule and
   * flips the GET to return it on the post-save reload. This is the exact shape
   * that triggers the loading-placeholder remount the bug rides on.
   */
  function routedFetch(): ReturnType<typeof vi.fn> {
    const feed = {
      plant_id: 1,
      care_type: "feed",
      interval_days: 14,
      winter_interval_days: null,
      dormancy: "paused",
      enabled: true,
      created_at: "2026-06-17T00:00:00Z",
      updated_at: "2026-06-17T00:00:01Z",
    };
    let saved = false;
    const fetchMock = vi
      .fn()
      .mockImplementation((_path: string, init?: { method?: string }) => {
        if ((init?.method ?? "GET") === "PUT") {
          saved = true;
          return Promise.resolve(okJson(feed));
        }
        return Promise.resolve(okJson(saved ? [feed] : []));
      });
    vi.stubGlobal("fetch", fetchMock);
    return fetchMock;
  }

  it("keeps unsaved Water values after the Feed section is saved", async () => {
    routedFetch();
    render(<CareScheduleModal plant={PLANT} onClose={() => undefined} />);
    await waitFor(() => {
      expect(screen.queryByText(/loading schedules/i)).not.toBeInTheDocument();
    });

    // Type a watering interval but do NOT save the Water section.
    const waterInterval =
      within(waterSection()).getByLabelText(/^interval \(days\)/i);
    fireEvent.change(waterInterval, { target: { value: "7" } });

    // Fill and save the Feed section, which triggers an upsert + reload.
    const feed = feedSection();
    fireEvent.change(within(feed).getByLabelText(/^interval \(days\)/i), {
      target: { value: "14" },
    });
    fireEvent.click(
      within(feed).getByRole("button", { name: /save the feed schedule/i }),
    );

    // Reload completed once the Feed section shows its Remove control (only
    // rendered for a persisted schedule).
    await waitFor(() => {
      expect(
        within(feedSection()).getByRole("button", {
          name: /remove the feed schedule/i,
        }),
      ).toBeInTheDocument();
    });

    // The unsaved Water interval must survive the sibling save.
    expect(
      within(waterSection()).getByLabelText(/^interval \(days\)/i),
    ).toHaveValue(7);
  });
});
