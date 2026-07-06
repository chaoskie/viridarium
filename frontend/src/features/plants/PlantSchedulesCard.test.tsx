import { fireEvent, render, screen } from "@testing-library/react";
import { describe, expect, it, vi } from "vitest";

import type { ScheduleDue } from "@/lib/api/plants";

import { PlantSchedulesCard } from "./PlantSchedulesCard";

function renderCard(
  schedules: readonly ScheduleDue[],
  onSetup: () => void = vi.fn(),
): void {
  render(<PlantSchedulesCard schedules={schedules} onSetup={onSetup} />);
}

describe("PlantSchedulesCard", () => {
  it("sched-due renders the date without overdue emphasis (F-10)", () => {
    renderCard([{ care_type: "water", next_due: "2026-07-10", overdue_days: 0 }]);

    expect(screen.getByText("Water")).toBeInTheDocument();
    expect(screen.getByText(/2026-07-10/)).toBeInTheDocument();
    expect(screen.queryByText(/overdue/i)).not.toBeInTheDocument();
  });

  it("sched-both renders distinct care types (F-10)", () => {
    renderCard([
      { care_type: "water", next_due: "2026-07-10", overdue_days: 0 },
      { care_type: "feed", next_due: "2026-07-01", overdue_days: 3 },
    ]);

    expect(screen.getByText("Water")).toBeInTheDocument();
    expect(screen.getByText("Feed")).toBeInTheDocument();
    expect(screen.getByText(/2026-07-10/)).toBeInTheDocument();
    expect(screen.getByText(/2026-07-01/)).toBeInTheDocument();
    expect(screen.getByText(/3 days overdue/i)).toBeInTheDocument();
  });

  it("sched-overdue is emphasized and not color-only (F-11, CRITICAL)", () => {
    renderCard([{ care_type: "feed", next_due: "2026-07-01", overdue_days: 5 }]);

    expect(screen.getByText(/2026-07-01/)).toBeInTheDocument();
    // The emphasis carries a textual label (FE-011: not hue alone).
    expect(screen.getByText(/5 days overdue/i)).toBeInTheDocument();
  });

  it("sched-paused shows a reason, no date, no overdue (F-12, CRITICAL)", () => {
    renderCard([{ care_type: "water", next_due: null, overdue_days: null }]);

    expect(screen.getByText("Water")).toBeInTheDocument();
    expect(screen.getByText(/paused/i)).toBeInTheDocument();
    expect(screen.queryByText(/overdue/i)).not.toBeInTheDocument();
    expect(screen.queryByText(/null/)).not.toBeInTheDocument();
    expect(screen.queryByText(/\d{4}-\d{2}-\d{2}/)).not.toBeInTheDocument();
  });

  it("sched-empty renders the setup affordance (F-12b, CRITICAL)", () => {
    const onSetup = vi.fn();
    renderCard([], onSetup);

    expect(screen.getByText(/no care schedules/i)).toBeInTheDocument();
    const setup = screen.getByRole("button", { name: /set up a schedule/i });
    fireEvent.click(setup);
    expect(onSetup).toHaveBeenCalledTimes(1);
  });
});
