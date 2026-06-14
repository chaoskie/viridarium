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
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
  cover_photo_id: null,
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
