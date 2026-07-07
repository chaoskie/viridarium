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

function okJson(status: number, body: unknown): Response {
  return {
    ok: true,
    status,
    json: () => Promise.resolve(body),
  } as Response;
}

function fail(status: number): Response {
  return {
    ok: false,
    status,
    json: () => Promise.resolve({ detail: "nope" }),
  } as Response;
}

interface StubOptions {
  /** Mutable holder so a PUT can change what the next plant GET returns. */
  readonly holder: { plant: Plant };
  readonly deleteResponse?: Response;
}

/** Route calls by path + method across everything the page and modals fetch. */
function stubApi({
  holder,
  deleteResponse,
}: StubOptions): ReturnType<typeof vi.fn> {
  const fetchMock = vi
    .fn()
    .mockImplementation((path: string, init?: RequestInit) => {
      const method = init?.method ?? "GET";
      if (path.endsWith("/timeline")) {
        return Promise.resolve(okJson(200, []));
      }
      if (path.endsWith("/photos")) {
        return Promise.resolve(okJson(200, []));
      }
      if (path.endsWith("/schedules")) {
        return Promise.resolve(okJson(200, []));
      }
      if (path.endsWith("/events")) {
        return Promise.resolve(
          method === "POST"
            ? okJson(201, {
                id: 1,
                plant_id: 3,
                type: "water",
                happened_on: "2026-07-06",
                note: null,
                photo_id: null,
                health: null,
                created_at: "2026-07-06T10:00:00Z",
              })
            : okJson(200, []),
        );
      }
      if (path.endsWith("/locations")) {
        return Promise.resolve(okJson(200, []));
      }
      if (method === "PUT") {
        const renamed = { ...holder.plant, name: "Renamed Fig" };
        holder.plant = renamed;
        return Promise.resolve(okJson(200, renamed));
      }
      if (method === "DELETE") {
        return Promise.resolve(deleteResponse ?? okJson(204, null));
      }
      return Promise.resolve(okJson(200, holder.plant));
    });
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

function plantGetCount(fetchMock: ReturnType<typeof vi.fn>): number {
  return fetchMock.mock.calls.filter((call) => {
    const path = call[0] as string;
    const method = (call[1] as RequestInit | undefined)?.method ?? "GET";
    return method === "GET" && /\/plants\/3$/.test(path);
  }).length;
}

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

async function ready(): Promise<void> {
  await waitFor(() => {
    expect(
      screen.getByRole("heading", { level: 1, name: /fiddle leaf fig/i }),
    ).toBeInTheDocument();
  });
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("PlantDetailPage action wiring", () => {
  it("each action opens its modal (F-14)", async () => {
    stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();

    const cases: readonly [RegExp, RegExp][] = [
      [/edit fiddle leaf fig/i, /edit plant/i],
      [/log care for fiddle leaf fig/i, /log care - fiddle leaf fig/i],
      [
        /configure care schedules for fiddle leaf fig/i,
        /schedules - fiddle leaf fig/i,
      ],
      [/view photos of fiddle leaf fig/i, /photos - fiddle leaf fig/i],
      [/delete fiddle leaf fig/i, /delete plant/i],
    ];
    for (const [action, title] of cases) {
      fireEvent.click(screen.getByRole("button", { name: action }));
      const dialog = await screen.findByRole("dialog", { name: title });
      expect(dialog).toBeInTheDocument();
      fireEvent.keyDown(document, { key: "Escape" });
      await waitFor(() => {
        expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
      });
    }
  });

  it("an edit mutation triggers a plant refetch (F-15, CRITICAL)", async () => {
    const holder = { plant: PLANT };
    const fetchMock = stubApi({ holder });
    renderAt("/plants/3");
    await ready();
    const before = plantGetCount(fetchMock);

    fireEvent.click(
      screen.getByRole("button", { name: /edit fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /edit plant/i });
    fireEvent.click(screen.getByRole("button", { name: /save changes/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { level: 1, name: /renamed fig/i }),
      ).toBeInTheDocument();
    });
    expect(plantGetCount(fetchMock)).toBe(before + 1);
  });

  it("logging a care event refetches the plant and bumps the timeline (F-15b, CRITICAL)", async () => {
    const fetchMock = stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();
    const before = plantGetCount(fetchMock);
    const timelineBefore = fetchMock.mock.calls.filter((call) =>
      (call[0] as string).endsWith("/timeline"),
    ).length;

    fireEvent.click(
      screen.getByRole("button", { name: /log care for fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /log care - fiddle leaf fig/i });
    fireEvent.click(screen.getByRole("button", { name: /log event/i }));

    await waitFor(() => {
      expect(plantGetCount(fetchMock)).toBe(before + 1);
    });
    await waitFor(() => {
      const timelineAfter = fetchMock.mock.calls.filter((call) =>
        (call[0] as string).endsWith("/timeline"),
      ).length;
      expect(timelineAfter).toBe(timelineBefore + 1);
    });
  });

  it("closing the schedules modal refetches the plant (F-16, CRITICAL)", async () => {
    const fetchMock = stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();
    const before = plantGetCount(fetchMock);

    fireEvent.click(
      screen.getByRole("button", {
        name: /configure care schedules for fiddle leaf fig/i,
      }),
    );
    await screen.findByRole("dialog", { name: /schedules/i });
    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(plantGetCount(fetchMock)).toBe(before + 1);
    });
  });

  it("closing the photos modal refetches the plant and bumps the timeline (F-16)", async () => {
    const fetchMock = stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();
    const before = plantGetCount(fetchMock);
    const timelineBefore = fetchMock.mock.calls.filter((call) =>
      (call[0] as string).endsWith("/timeline"),
    ).length;

    fireEvent.click(
      screen.getByRole("button", { name: /view photos of fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /photos - fiddle leaf fig/i });
    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(plantGetCount(fetchMock)).toBe(before + 1);
    });
    await waitFor(() => {
      const timelineAfter = fetchMock.mock.calls.filter((call) =>
        (call[0] as string).endsWith("/timeline"),
      ).length;
      expect(timelineAfter).toBe(timelineBefore + 1);
    });
  });

  it("a confirmed delete navigates to /plants (F-17, CRITICAL)", async () => {
    const fetchMock = stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();

    fireEvent.click(
      screen.getByRole("button", { name: /delete fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /delete plant/i });
    fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(
        screen.getByRole("heading", { name: /plants list landing/i }),
      ).toBeInTheDocument();
    });
    const deletes = fetchMock.mock.calls.filter(
      (call) => (call[1] as RequestInit | undefined)?.method === "DELETE",
    );
    expect(deletes).toHaveLength(1);
  });

  it("cancelling the edit modal does not refetch spuriously (F-18)", async () => {
    const fetchMock = stubApi({ holder: { plant: PLANT } });
    renderAt("/plants/3");
    await ready();
    const before = plantGetCount(fetchMock);

    fireEvent.click(
      screen.getByRole("button", { name: /edit fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /edit plant/i });
    fireEvent.keyDown(document, { key: "Escape" });

    await waitFor(() => {
      expect(screen.queryByRole("dialog")).not.toBeInTheDocument();
    });
    expect(plantGetCount(fetchMock)).toBe(before);
    expect(
      screen.getByRole("heading", { level: 1, name: /fiddle leaf fig/i }),
    ).toBeInTheDocument();
  });

  it("a failed delete keeps the page (F-19)", async () => {
    stubApi({ holder: { plant: PLANT }, deleteResponse: fail(500) });
    renderAt("/plants/3");
    await ready();

    fireEvent.click(
      screen.getByRole("button", { name: /delete fiddle leaf fig/i }),
    );
    await screen.findByRole("dialog", { name: /delete plant/i });
    fireEvent.click(screen.getByRole("button", { name: /^delete$/i }));

    await waitFor(() => {
      expect(
        screen.getByText(/could not delete this plant/i),
      ).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("heading", { name: /plants list landing/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.getByRole("heading", { level: 1, name: /fiddle leaf fig/i }),
    ).toBeInTheDocument();
  });
});
