import { render, screen, waitFor } from "@testing-library/react";
import { MemoryRouter } from "react-router-dom";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import { PlantsPage } from "./PlantsPage";

function plant(id: number, name: string): Plant {
  return {
    id,
    name,
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
    schedules: [],
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  };
}

const PLANTS: Plant[] = [plant(1, "Fern"), plant(2, "Monstera")];

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

/** The list GET returns the plants; the locations GET returns []. */
function stubList(): void {
  const fetchMock = vi
    .fn()
    .mockImplementation((path: string) =>
      Promise.resolve(
        path.includes("/locations") ? okJson(200, []) : okJson(200, PLANTS),
      ),
    );
  vi.stubGlobal("fetch", fetchMock);
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("PlantsPage detail link (AC5, F-12)", () => {
  it("links each plant to its detail page at /plants/{id}", async () => {
    stubList();
    render(
      <MemoryRouter initialEntries={["/plants"]}>
        <PlantsPage />
      </MemoryRouter>,
    );

    const fernLink = await screen.findByRole("link", {
      name: /view fern's history/i,
    });
    expect(fernLink).toHaveAttribute("href", "/plants/1");

    await waitFor(() => {
      expect(
        screen.getByRole("link", { name: /view monstera's history/i }),
      ).toHaveAttribute("href", "/plants/2");
    });
  });
});
