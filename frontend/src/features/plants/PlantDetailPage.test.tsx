import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter, Route, Routes } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { PlantDetailPage } from "./PlantDetailPage";

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
  cover_photo_id: null,
  schedules: [],
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

const PLANT_FULL: Plant = {
  ...PLANT,
  species: "Ficus lyrata",
  acquired_on: "2025-03-14",
  light_level: "bright-indirect",
  tags: ["rare"],
  schedules: [{ care_type: "water", next_due: "2026-07-10", overdue_days: 0 }],
};

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

/** Route GETs by path: plant vs timeline vs photos vs locations. */
function stubByPath(plant: Plant = PLANT): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockImplementation((path: string) => {
    if (path.endsWith("/timeline")) {
      return Promise.resolve(okJson(200, []));
    }
    if (path.endsWith("/photos")) {
      return Promise.resolve(okJson(200, []));
    }
    if (path.endsWith("/locations")) {
      return Promise.resolve(okJson(200, []));
    }
    return Promise.resolve(okJson(200, plant));
  });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

/** Render the app router scoped to the detail route + a list landing page. */
function renderAt(path: string): void {
  render(
    <MemoryRouter initialEntries={[path]}>
      <Routes>
        <Route path="/plants/:id" element={<PlantDetailPage />} />
        <Route path="/plants" element={<h1>Plants list landing</h1>} />
      </Routes>
    </MemoryRouter>,
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("PlantDetailPage", () => {
  it("is reachable at /plants/:id and hosts the timeline for that id (F-10)", async () => {
    const fetchMock = stubByPath();
    renderAt("/plants/3");

    // The timeline fires exactly one GET for plant 3's timeline.
    await waitFor(() => {
      const timelineCalls = fetchMock.mock.calls.filter((call) =>
        (call[0] as string).endsWith("/plants/3/timeline"),
      );
      expect(timelineCalls).toHaveLength(1);
    });
  });

  it("shows the decorative outer pot when set (cachepot, relocated to the attributes card)", async () => {
    stubByPath({
      ...PLANT,
      outer_pot_material: "ceramic",
      outer_pot_size_cm: 18,
    });
    renderAt("/plants/3");

    await waitFor(() => {
      expect(screen.getByText(/ceramic \(18 cm\)/i)).toBeInTheDocument();
    });
    expect(screen.getByText("Outer pot")).toBeInTheDocument();
  });

  it("shows the plant name in the header and a back link to the list (F-11/F-24)", async () => {
    stubByPath();
    renderAt("/plants/3");

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: /fiddle leaf fig/i }),
      ).toBeInTheDocument();
    });

    const back = screen.getByRole("link", { name: /back to plants/i });
    fireEvent.click(back);

    expect(
      screen.getByRole("heading", { name: /plants list landing/i }),
    ).toBeInTheDocument();
  });

  it("mounts the FULL page for a valid id (F-20)", async () => {
    stubByPath(PLANT_FULL);
    renderAt("/plants/3");

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: /fiddle leaf fig/i }),
      ).toBeInTheDocument();
    });
    // Attributes card
    expect(screen.getAllByText("Ficus lyrata").length).toBeGreaterThan(0);
    expect(screen.getByText("2025-03-14")).toBeInTheDocument();
    // Schedules card
    expect(screen.getByText(/care schedules/i)).toBeInTheDocument();
    expect(screen.getByText(/2026-07-10/)).toBeInTheDocument();
    // Gallery section (empty state here - no photos stubbed)
    await waitFor(() => {
      expect(screen.getByText(/no photos yet/i)).toBeInTheDocument();
    });
    // Timeline section
    expect(screen.getByText(/history/i)).toBeInTheDocument();
  });

  it("renders a loading state before the plant resolves, not a not-found flash (F-21)", () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockImplementation(() => new Promise(() => undefined)),
    );
    renderAt("/plants/3");

    expect(screen.getByText(/loading/i)).toBeInTheDocument();
    expect(
      screen.queryByText(/could not be found/i),
    ).not.toBeInTheDocument();
  });

  it("renders a graceful not-found shell when the fetch fails (F-22)", async () => {
    vi.stubGlobal(
      "fetch",
      vi.fn().mockResolvedValue({
        ok: false,
        status: 404,
        json: () => Promise.resolve({ detail: "gone" }),
      } as Response),
    );
    renderAt("/plants/999");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /could not be found/i,
      );
    });
  });

  it("keeps the existing not-found handling for an invalid id, no fetch (F-23)", async () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderAt("/plants/abc");

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(
        /could not be found/i,
      );
    });
    const plantCalls = fetchMock.mock.calls.filter((call) =>
      (call[0] as string).includes("/plants/"),
    );
    expect(plantCalls).toHaveLength(0);
  });
});
