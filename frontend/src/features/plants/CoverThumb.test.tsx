import { render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { CoverThumb } from "./PlantsPage";

const BASE: Plant = {
  id: 7,
  name: "Monstera",
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

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("CoverThumb (AC4: no per-card photo fetch)", () => {
  it("renders the cover image from plant.cover_photo_id without fetching", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<CoverThumb plant={{ ...BASE, cover_photo_id: 42 }} />);

    const img = screen.getByRole("img", { name: /monstera cover photo/i });
    expect(img).toHaveAttribute("src", "/api/v1/plants/7/photos/42");
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("renders the placeholder when cover_photo_id is null without fetching", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(<CoverThumb plant={{ ...BASE, cover_photo_id: null }} />);

    expect(screen.getByText(/no photo/i)).toBeInTheDocument();
    expect(screen.queryByRole("img")).not.toBeInTheDocument();
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("fires zero photo requests for a list of plants", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);

    render(
      <ul>
        <li>
          <CoverThumb plant={{ ...BASE, id: 1, cover_photo_id: 10 }} />
        </li>
        <li>
          <CoverThumb plant={{ ...BASE, id: 2, cover_photo_id: null }} />
        </li>
        <li>
          <CoverThumb plant={{ ...BASE, id: 3, cover_photo_id: 30 }} />
        </li>
      </ul>,
    );

    expect(fetchMock).not.toHaveBeenCalled();
  });
});
