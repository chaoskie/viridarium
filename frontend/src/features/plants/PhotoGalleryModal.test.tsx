import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Photo } from "@/lib/api/photos";
import type { Plant } from "@/lib/api/plants";

import { PhotoGalleryModal } from "./PhotoGalleryModal";

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
  cover_photo_id: 11,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

const PHOTOS: Photo[] = [
  {
    id: 12,
    plant_id: 1,
    content_type: "image/jpeg",
    size_bytes: 2048,
    is_cover: false,
    created_at: "2026-06-17T09:00:00Z",
    url: "/api/v1/plants/1/photos/12",
  },
  {
    id: 11,
    plant_id: 1,
    content_type: "image/jpeg",
    size_bytes: 4096,
    is_cover: true,
    created_at: "2026-06-16T09:00:00Z",
    url: "/api/v1/plants/1/photos/11",
  },
];

function okJson(body: unknown): Response {
  return {
    ok: true,
    status: 200,
    json: () => Promise.resolve(body),
  } as Response;
}

async function renderWithPhotos(): Promise<void> {
  vi.stubGlobal("fetch", vi.fn().mockResolvedValue(okJson(PHOTOS)));
  render(<PhotoGalleryModal plant={PLANT} onClose={() => undefined} />);
  await waitFor(() => {
    expect(screen.queryByText(/loading photos/i)).not.toBeInTheDocument();
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

/** The thumbnail "view full size" buttons (one per photo). */
function viewButtons(): HTMLElement[] {
  return screen.getAllByRole("button", {
    name: /view this photo .* at full size/i,
  });
}

/** The first thumbnail's "view full size" button (definite, for clicking). */
function firstViewButton(): HTMLElement {
  const [first] = viewButtons();
  if (first === undefined) {
    throw new Error("expected at least one thumbnail view button");
  }
  return first;
}

describe("PhotoGalleryModal full-image view (BUG-008)", () => {
  it("opens the full, uncropped image when a thumbnail is selected", async () => {
    await renderWithPhotos();

    // Each thumbnail is a button that opens the full image.
    expect(viewButtons()).toHaveLength(2);

    fireEvent.click(firstViewButton());

    // The full-size image of the selected photo is shown...
    const full = await screen.findByRole("img", {
      name: /fern photo, full size/i,
    });
    expect(full).toBeInTheDocument();
    expect(full).toHaveAttribute("src", "/api/v1/plants/1/photos/12");

    // ...and a control returns to the grid.
    expect(
      screen.getByRole("button", { name: /back to all photos/i }),
    ).toBeInTheDocument();
  });

  it("returns to the grid when Back is clicked", async () => {
    await renderWithPhotos();

    fireEvent.click(firstViewButton());

    fireEvent.click(
      screen.getByRole("button", { name: /back to all photos/i }),
    );

    // Grid is back: the thumbnail view buttons are present again and the
    // full-size image is gone.
    await waitFor(() => {
      expect(viewButtons()).toHaveLength(2);
    });
    expect(
      screen.queryByRole("img", { name: /fern photo, full size/i }),
    ).not.toBeInTheDocument();
  });
});
