import { render, screen, within } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";

import { App } from "@/App";

describe("App shell", () => {
  beforeEach(() => {
    // Keep the Today page's plants/locations requests from hitting the network
    // during the shell smoke tests; an empty list settles to the empty-state.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      } as Response),
    );
  });

  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("renders the header primary nav with all placeholders", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    const nav = screen.getByRole("navigation", { name: "Primary" });
    for (const label of ["Today", "Plants", "Rooms", "Journal", "Settings"]) {
      expect(
        within(nav).getByRole("link", { name: label }),
      ).toBeInTheDocument();
    }
  });

  it("renders a phone bottom-nav with the same destinations (responsive)", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    // Both nav patterns render in the DOM; CSS hides one per breakpoint.
    const bottomNav = screen.getByRole("navigation", {
      name: "Primary mobile",
    });
    for (const label of ["Today", "Plants", "Rooms", "Journal", "Settings"]) {
      expect(
        within(bottomNav).getByRole("link", { name: label }),
      ).toBeInTheDocument();
    }
  });

  it("renders the Today page at the root route", async () => {
    // The Today view (US-4.1) loads plants + locations; with an empty list it
    // settles on the friendly empty-state.
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: true,
        status: 200,
        json: () => Promise.resolve([]),
      } as Response),
    );
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    expect(
      screen.getByRole("heading", { level: 1, name: /^Today$/i }),
    ).toBeInTheDocument();
    await screen.findByText(/nothing due/i);
  });

  it("uses plain-English functional labels only - no Latin (D-008)", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    // Latin functional labels from the mockup must NOT appear in the app.
    for (const latin of [
      "HODIE",
      "TRICLINIUM",
      "CULINA",
      "TABLINUM",
      "AQUATA",
      "NEGLECTAE",
      "PLANTAE",
      "HORTUS",
    ]) {
      expect(screen.queryByText(latin)).not.toBeInTheDocument();
    }

    // The wordmark is the only sanctioned Latin (accessible name spans split).
    expect(screen.getByText(/VIRID/)).toBeInTheDocument();
  });

  it("renders the theme selector in the shell (reachable on mobile)", () => {
    render(
      <MemoryRouter initialEntries={["/"]}>
        <App />
      </MemoryRouter>,
    );

    // Toggle appears in both header layouts; at least one is present.
    expect(screen.getAllByLabelText("Theme").length).toBeGreaterThan(0);
  });
});
