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
  light_level: null,
  notes: null,
  tags: [],
  archived: false,
  cover_photo_id: null,
  created_at: "2026-06-08T10:00:00Z",
  updated_at: "2026-06-08T10:00:00Z",
};

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

/** Route the GET by path: the plant get vs the timeline. */
function stubByPath(): ReturnType<typeof vi.fn> {
  const fetchMock = vi
    .fn()
    .mockImplementation((path: string) =>
      Promise.resolve(
        path.endsWith("/timeline") ? okJson(200, []) : okJson(200, PLANT),
      ),
    );
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

  it("shows the plant name in the header and a back link to the list (F-11)", async () => {
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
});
