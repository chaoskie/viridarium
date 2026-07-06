import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Photo } from "@/lib/api/photos";
import type { Plant } from "@/lib/api/plants";

import { PlantGallery, THUMB_CAP } from "./PlantGallery";

const PLANT: Plant = {
  id: 3,
  name: "Fiddle Leaf Fig",
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
  cover_photo_id: 1,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

function makePhotos(count: number): Photo[] {
  return Array.from({ length: count }, (_, i) => ({
    id: i + 1,
    plant_id: 3,
    content_type: "image/jpeg",
    size_bytes: 1000,
    is_cover: i === 0,
    created_at: "2026-06-08T10:00:00Z",
    url: `/api/v1/plants/3/photos/${String(i + 1)}`,
  }));
}

function stubPhotos(photos: readonly Photo[]): void {
  vi.stubGlobal(
    "fetch",
    vi.fn().mockResolvedValue({
      ok: true,
      status: 200,
      json: () => Promise.resolve(photos),
    } as Response),
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("PlantGallery", () => {
  it("gal-cover-thumbs renders the cover plus a thumb per remaining photo (F-13a)", async () => {
    stubPhotos(makePhotos(4));
    const onOpen = vi.fn();
    render(<PlantGallery plant={PLANT} onOpen={onOpen} />);

    const cover = await screen.findByAltText("Fiddle Leaf Fig cover photo");
    expect(cover).toHaveAttribute("src", "/api/v1/plants/3/photos/1");
    // 3 remaining photos -> 3 thumbs, no overflow affordance.
    expect(screen.getAllByAltText(/Fiddle Leaf Fig photo/)).toHaveLength(3);
    expect(screen.queryByText(/^\+\d+$/)).not.toBeInTheDocument();
  });

  it("gal-overflow caps the strip and shows a correct +N that opens the modal (F-13b, CRITICAL)", async () => {
    const total = THUMB_CAP + 4; // cover + CAP thumbs + 3 hidden
    stubPhotos(makePhotos(total));
    const onOpen = vi.fn();
    render(<PlantGallery plant={PLANT} onOpen={onOpen} />);

    await screen.findByAltText("Fiddle Leaf Fig cover photo");
    expect(screen.getAllByAltText(/Fiddle Leaf Fig photo/)).toHaveLength(
      THUMB_CAP,
    );
    const overflow = screen.getByRole("button", {
      name: new RegExp(`view all ${String(total)} photos`, "i"),
    });
    expect(overflow).toHaveTextContent("+3");
    fireEvent.click(overflow);
    expect(onOpen).toHaveBeenCalledTimes(1);
  });

  it("gal-cover-only renders no strip and no +N", async () => {
    stubPhotos(makePhotos(1));
    render(<PlantGallery plant={PLANT} onOpen={vi.fn()} />);

    await screen.findByAltText("Fiddle Leaf Fig cover photo");
    expect(
      screen.queryByAltText(/Fiddle Leaf Fig photo/),
    ).not.toBeInTheDocument();
    expect(screen.queryByText(/^\+\d+$/)).not.toBeInTheDocument();
  });

  it("gal-no-cover-has-photos falls back to the first photo", async () => {
    const photos = makePhotos(3).map((p) => ({ ...p, is_cover: false }));
    stubPhotos(photos);
    render(
      <PlantGallery plant={{ ...PLANT, cover_photo_id: null }} onOpen={vi.fn()} />,
    );

    const prominent = await screen.findByAltText("Fiddle Leaf Fig cover photo");
    expect(prominent).toHaveAttribute("src", "/api/v1/plants/3/photos/1");
    expect(screen.getAllByAltText(/Fiddle Leaf Fig photo/)).toHaveLength(2);
  });

  it("gal-empty renders the empty state without broken images or auto-open (F-13c, CRITICAL)", async () => {
    stubPhotos([]);
    const onOpen = vi.fn();
    render(
      <PlantGallery plant={{ ...PLANT, cover_photo_id: null }} onOpen={onOpen} />,
    );

    expect(await screen.findByText(/no photos yet/i)).toBeInTheDocument();
    expect(document.querySelector("img")).toBeNull();
    expect(onOpen).not.toHaveBeenCalled();
  });

  it("gal-open-modal: tapping the cover or a thumb calls onOpen (F-13d)", async () => {
    stubPhotos(makePhotos(3));
    const onOpen = vi.fn();
    render(<PlantGallery plant={PLANT} onOpen={onOpen} />);

    fireEvent.click(await screen.findByAltText("Fiddle Leaf Fig cover photo"));
    fireEvent.click(screen.getAllByAltText(/Fiddle Leaf Fig photo/)[0]!);
    expect(onOpen).toHaveBeenCalledTimes(2);
  });
});
