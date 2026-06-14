import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CareEvent } from "@/lib/api/careEvents";
import type { Plant } from "@/lib/api/plants";

import { QuickCareActions } from "./QuickCareActions";

const PLANT: Plant = {
  id: 1,
  name: "Fern",
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

/** Today's local calendar date as YYYY-MM-DD (independent oracle). */
function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

function createdEvent(type: CareEvent["type"]): CareEvent {
  return {
    id: 5,
    plant_id: 1,
    type,
    happened_on: localToday(),
    note: null,
    photo_id: null,
    health: null,
    created_at: "2026-06-11T10:00:00Z",
  };
}

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
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("QuickCareActions", () => {
  it("one-tap Water POSTs today's water event and confirms inline (F-16)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("water")));
    vi.stubGlobal("fetch", fetchMock);
    render(<QuickCareActions plant={PLANT} />);

    fireEvent.click(screen.getByRole("button", { name: /log water/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/logged water/i);
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v1/plants/1/events");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      type: "water",
      happened_on: localToday(),
    });
  });

  it("one-tap Feed POSTs today's feed event (F-16)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("feed")));
    vi.stubGlobal("fetch", fetchMock);
    render(<QuickCareActions plant={PLANT} />);

    fireEvent.click(screen.getByRole("button", { name: /log feed/i }));

    await waitFor(() => {
      expect(screen.getByRole("status")).toHaveTextContent(/logged feed/i);
    });
    expect(
      JSON.parse(
        (fetchMock.mock.calls[0] as [string, RequestInit])[1].body as string,
      ),
    ).toEqual({ type: "feed", happened_on: localToday() });
  });

  it("surfaces a non-blocking error on a failed tap; the card stays usable (F-17)", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(fail(500)));
    render(<QuickCareActions plant={PLANT} />);

    const water = screen.getByRole("button", { name: /log water/i });
    fireEvent.click(water);

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(water).toBeEnabled();
    expect(screen.getByRole("button", { name: /log feed/i })).toBeEnabled();
  });

  it("opens the LogCareModal as the expanded entry point", () => {
    render(<QuickCareActions plant={PLANT} />);

    fireEvent.click(screen.getByRole("button", { name: /log care/i }));

    expect(
      screen.getByRole("dialog", { name: /log care - fern/i }),
    ).toBeInTheDocument();
  });
});
