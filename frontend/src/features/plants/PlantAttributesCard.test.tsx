import { render, screen } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { describe, expect, it } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { PlantAttributesCard } from "./PlantAttributesCard";

const PLANT_EMPTY: Plant = {
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
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

const PLANT_FULL: Plant = {
  ...PLANT_EMPTY,
  species: "Ficus lyrata",
  location_id: 2,
  acquired_on: "2025-03-14",
  pot_size_cm: 14,
  pot_material: "terracotta",
  outer_pot_material: "ceramic",
  outer_pot_size_cm: 18,
  light_level: "bright-indirect",
  notes: "Sensitive to drafts.",
  tags: ["rare", "office"],
};

function renderCard(plant: Plant, locationName: string | null = null): void {
  render(
    <MemoryRouter>
      <PlantAttributesCard plant={plant} locationName={locationName} />
    </MemoryRouter>,
  );
}

describe("PlantAttributesCard", () => {
  it("attr-full renders every attribute row (F-5)", () => {
    renderCard(PLANT_FULL, "Living room");

    expect(screen.getByText("Ficus lyrata")).toBeInTheDocument();
    expect(screen.getByText("Living room")).toBeInTheDocument();
    expect(screen.getByText("2025-03-14")).toBeInTheDocument();
    expect(screen.getByText(/14 cm terracotta/i)).toBeInTheDocument();
    expect(screen.getByText(/ceramic \(18 cm\)/i)).toBeInTheDocument();
    expect(screen.getByText(/bright-indirect/i)).toBeInTheDocument();
    expect(screen.getByText("Sensitive to drafts.")).toBeInTheDocument();
    expect(screen.getByText("rare")).toBeInTheDocument();
    expect(screen.getByText("office")).toBeInTheDocument();
  });

  it("attr-empty renders NO empty rows (F-6, CRITICAL)", () => {
    renderCard(PLANT_EMPTY);

    for (const label of [
      "Species",
      "Room",
      "Acquired",
      "Pot",
      "Outer pot",
      "Light",
      "Notes",
      "Tags",
    ]) {
      expect(screen.queryByText(label)).not.toBeInTheDocument();
    }
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
    expect(screen.queryByText(/—/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\(\s*cm\)/)).not.toBeInTheDocument();
  });

  it("attr-cachepot-material-only omits the size suffix (F-7, CRITICAL)", () => {
    renderCard({
      ...PLANT_EMPTY,
      outer_pot_material: "ceramic",
      outer_pot_size_cm: null,
    });

    expect(screen.getByText("Outer pot")).toBeInTheDocument();
    expect(screen.getByText("ceramic")).toBeInTheDocument();
    expect(screen.queryByText(/null cm/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/\(\s*cm\)/)).not.toBeInTheDocument();
  });

  it("attr-cachepot-full and attr-inner-pot-partial render only set parts (F-8)", () => {
    renderCard({
      ...PLANT_EMPTY,
      pot_size_cm: 14,
      pot_material: null,
      outer_pot_material: "ceramic",
      outer_pot_size_cm: 18,
    });

    expect(screen.getByText(/ceramic \(18 cm\)/i)).toBeInTheDocument();
    expect(screen.getByText("14 cm")).toBeInTheDocument();
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
  });

  it("attr-tags-empty hides the tags block; attr-single-tag renders one chip (F-9)", () => {
    renderCard({ ...PLANT_EMPTY, notes: "Water sparingly." });
    expect(screen.queryByText("Tags")).not.toBeInTheDocument();
    expect(screen.getByText("Water sparingly.")).toBeInTheDocument();
    expect(screen.queryByText("Species")).not.toBeInTheDocument();
  });

  it("attr-single-tag renders exactly one chip (F-9)", () => {
    renderCard({ ...PLANT_EMPTY, tags: ["office"] });
    expect(screen.getByText("Tags")).toBeInTheDocument();
    expect(screen.getByText("office")).toBeInTheDocument();
  });
});
