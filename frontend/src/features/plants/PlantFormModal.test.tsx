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
