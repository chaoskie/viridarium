import { fireEvent, render, screen } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

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

describe("PlantFormModal pot size validation (VIRIDARIUM-47)", () => {
  it("rejects a decimal pot size with a field error and never submits", async () => {
    const onSubmit = renderCreateModal();

    fireEvent.change(screen.getByLabelText(/name/i), {
      target: { value: "Monstera" },
    });
    fireEvent.change(screen.getByLabelText(/pot size/i), {
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
    fireEvent.change(screen.getByLabelText(/pot size/i), {
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
