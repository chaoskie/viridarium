import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { PlantFormModal } from "./PlantFormModal";

afterEach(() => {
  vi.restoreAllMocks();
});

function renderCreateModal(onSubmit = vi.fn()) {
  render(
    <PlantFormModal locations={[]} onSubmit={onSubmit} onClose={vi.fn()} />,
  );
  return onSubmit;
}

function renderEditModal(plant: Plant, onSubmit = vi.fn()) {
  render(
    <PlantFormModal
      plant={plant}
      locations={[]}
      onSubmit={onSubmit}
      onClose={vi.fn()}
    />,
  );
  return onSubmit;
}

const PLANT_WITH_OUTER_POT: Plant = {
  id: 1,
  name: "Monstera",
  species: null,
  location_id: null,
  acquired_on: null,
  pot_size_cm: 14,
  pot_material: "plastic",
  outer_pot_material: "ceramic",
  outer_pot_size_cm: 20,
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

describe("PlantFormModal pot size validation (VIRIDARIUM-47)", () => {
  it("rejects a decimal pot size with a field error and never submits", async () => {
    const onSubmit = renderCreateModal();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Monstera" },
    });
    fireEvent.change(screen.getByLabelText(/^pot size/i), {
      target: { value: "3.7" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    expect(await screen.findByRole("alert")).toHaveTextContent(/whole number/i);
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("submits an integer pot size unchanged", async () => {
    const onSubmit = renderCreateModal(vi.fn().mockResolvedValue(undefined));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Monstera" },
    });
    fireEvent.change(screen.getByLabelText(/^pot size/i), {
      target: { value: "14" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ pot_size_cm: 14 });
  });
});

describe("PlantFormModal acquired-on is optional (BUG-004)", () => {
  it("labels the date field optional and explains a blank is allowed", () => {
    renderCreateModal();

    expect(
      screen.getByLabelText(/acquired on \(optional\)/i),
    ).toBeInTheDocument();
    expect(
      screen.getByText(/leave blank if you don't know/i),
    ).toBeInTheDocument();
  });
});

// Characterisation tests (not red-first): they guard the form's *existing*
// partial-fill / required-name / input-cap behaviour, added in response to the
// soak input-hardening question. No production change in this batch drives them;
// the TEST-014 deviation is recorded in the change worklog (comply-or-explain).
describe("PlantFormModal partial fill and required-name guard", () => {
  it("submits with only the name filled - every other field is optional", async () => {
    const onSubmit = renderCreateModal(vi.fn().mockResolvedValue(undefined));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Pothos" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({ name: "Pothos" });
  });

  it("blocks submit and explains when the name is empty", async () => {
    const onSubmit = renderCreateModal();

    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    expect(await screen.findByText(/enter a plant name/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });

  it("blocks submit when the name is only whitespace", async () => {
    const onSubmit = renderCreateModal();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "   " },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    expect(await screen.findByText(/enter a plant name/i)).toBeInTheDocument();
    expect(onSubmit).not.toHaveBeenCalled();
  });
});

describe("PlantFormModal input-length hardening", () => {
  it("caps the text inputs at their server max lengths", () => {
    renderCreateModal();

    expect(screen.getByLabelText(/name/i)).toHaveAttribute("maxlength", "120");
    expect(screen.getByLabelText(/species/i)).toHaveAttribute(
      "maxlength",
      "200",
    );
    expect(screen.getByLabelText(/notes/i)).toHaveAttribute(
      "maxlength",
      "10000",
    );
  });
});

// Outer / decorative pot (cachepot) section - NEW behaviour (plant-cachepot,
// G6). F4-F8 assert new behaviour and are genuinely red-first: the
// characterisation carve-out does NOT apply (test-foundation §8).
describe("PlantFormModal outer (decorative) pot (plant-cachepot)", () => {
  it("sets the outer material + size and submits them (F4)", async () => {
    const onSubmit = renderCreateModal(vi.fn().mockResolvedValue(undefined));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Monstera" },
    });
    fireEvent.change(screen.getByLabelText(/outer.*pot material/i), {
      target: { value: "woven" },
    });
    fireEvent.change(screen.getByLabelText(/outer.*pot size/i), {
      target: { value: "22" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
      outer_pot_material: "woven",
      outer_pot_size_cm: 22,
    });
  });

  it("submits null outer pot fields when left unset (F5)", async () => {
    const onSubmit = renderCreateModal(vi.fn().mockResolvedValue(undefined));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Pothos" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
      outer_pot_material: null,
      outer_pot_size_cm: null,
    });
  });

  it("clears a previously-set outer pot back to null (F6)", async () => {
    const onSubmit = renderEditModal(
      PLANT_WITH_OUTER_POT,
      vi.fn().mockResolvedValue(undefined),
    );

    fireEvent.change(screen.getByLabelText(/outer.*pot material/i), {
      target: { value: "" },
    });
    fireEvent.change(screen.getByLabelText(/outer.*pot size/i), {
      target: { value: "" },
    });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
      outer_pot_material: null,
      outer_pot_size_cm: null,
    });
  });

  it("submits null for a decimal outer size via parseOptionalInt (F7)", async () => {
    const onSubmit = renderCreateModal(vi.fn().mockResolvedValue(undefined));

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Monstera" },
    });
    fireEvent.change(screen.getByLabelText(/outer.*pot size/i), {
      target: { value: "3.7" },
    });
    fireEvent.click(screen.getByRole("button", { name: /add plant/i }));

    await vi.waitFor(() => {
      expect(onSubmit).toHaveBeenCalledTimes(1);
    });
    expect(onSubmit.mock.calls[0]?.[0]).toMatchObject({
      outer_pot_size_cm: null,
    });
  });

  it("relabels the inner pot and adds an outer pot section (F8)", () => {
    renderCreateModal();

    expect(screen.getByText(/nursery \(inner\) pot/i)).toBeInTheDocument();
    expect(screen.getByText(/outer \/ decorative pot/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/outer.*pot material/i)).toBeInTheDocument();
    expect(screen.getByLabelText(/outer.*pot size/i)).toBeInTheDocument();
  });
});
