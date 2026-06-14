import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { CareEvent } from "@/lib/api/careEvents";
import type { Photo } from "@/lib/api/photos";
import type { Plant } from "@/lib/api/plants";

import { LogCareModal } from "./LogCareModal";

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

const EVENT: CareEvent = {
  id: 5,
  plant_id: 1,
  type: "water",
  happened_on: "2026-06-11",
  note: null,
  photo_id: null,
  health: null,
  created_at: "2026-06-11T10:00:00Z",
};

const PHOTO: Photo = {
  id: 10,
  plant_id: 1,
  content_type: "image/jpeg",
  size_bytes: 3,
  is_cover: false,
  created_at: "2026-06-11T10:00:00Z",
  url: "/api/v1/plants/1/photos/10",
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
    json: () => Promise.resolve({ detail: "boom" }),
  } as Response;
}

/** Today's local calendar date as YYYY-MM-DD (independent oracle). */
function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

function renderModal(overrides?: {
  onLogged?: (event: CareEvent) => void;
  onClose?: () => void;
}): { onLogged: ReturnType<typeof vi.fn>; onClose: ReturnType<typeof vi.fn> } {
  const onLogged = vi.fn();
  const onClose = vi.fn();
  render(
    <LogCareModal
      plant={PLANT}
      onLogged={overrides?.onLogged ?? onLogged}
      onClose={overrides?.onClose ?? onClose}
    />,
  );
  return { onLogged, onClose };
}

function submit(): void {
  fireEvent.click(screen.getByRole("button", { name: /log event/i }));
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("LogCareModal form", () => {
  it("offers the four event types in the type select (F-8)", () => {
    renderModal();

    const select = screen.getByLabelText<HTMLSelectElement>(/type/i);
    const values = [...select.options].map((option) => option.value);
    expect(values).toEqual(["water", "feed", "repot", "observe"]);
  });

  it("shows the health select ONLY for observe (F-9)", () => {
    renderModal();

    // Default type is water: no health control.
    expect(screen.queryByLabelText(/health/i)).not.toBeInTheDocument();

    const select = screen.getByLabelText(/type/i);
    fireEvent.change(select, { target: { value: "observe" } });
    expect(screen.getByLabelText(/health/i)).toBeInTheDocument();

    for (const type of ["water", "feed", "repot"]) {
      fireEvent.change(select, { target: { value: type } });
      expect(screen.queryByLabelText(/health/i)).not.toBeInTheDocument();
    }
  });

  it("date defaults to today and caps max at today (F-10)", () => {
    renderModal();

    const today = localToday();
    const date = screen.getByLabelText<HTMLInputElement>(/date/i);
    expect(date.value).toBe(today);
    expect(date).toHaveAttribute("max", today);
  });

  it("blocks a future date on submit without firing a POST (F-11)", () => {
    const fetchMock = vi.fn();
    vi.stubGlobal("fetch", fetchMock);
    renderModal();

    fireEvent.change(screen.getByLabelText(/date/i), {
      target: { value: "2999-01-01" },
    });
    submit();

    expect(screen.getByRole("alert")).toHaveTextContent(/future/i);
    expect(fetchMock).not.toHaveBeenCalled();
  });

  it("submits the assembled expanded event and closes on success (F-12)", async () => {
    const today = localToday();
    const created: CareEvent = {
      ...EVENT,
      type: "observe",
      note: "New leaf unfurling",
      health: "good",
      happened_on: today,
    };
    const fetchMock = vi.fn().mockResolvedValue(okJson(201, created));
    vi.stubGlobal("fetch", fetchMock);
    const { onLogged, onClose } = renderModal();

    fireEvent.change(screen.getByLabelText(/type/i), {
      target: { value: "observe" },
    });
    fireEvent.change(screen.getByLabelText(/note/i), {
      target: { value: "New leaf unfurling" },
    });
    fireEvent.change(screen.getByLabelText(/health/i), {
      target: { value: "good" },
    });
    submit();

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
    expect(fetchMock).toHaveBeenCalledTimes(1);
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v1/plants/1/events");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      type: "observe",
      happened_on: today,
      note: "New leaf unfurling",
      health: "good",
    });
    expect(onLogged).toHaveBeenCalledWith(created);
  });

  it("uploads the photo first, then creates the event with its photo_id (F-13)", async () => {
    const today = localToday();
    const fetchMock = vi
      .fn()
      .mockImplementation((path: string) =>
        Promise.resolve(
          path.endsWith("/photos")
            ? okJson(201, PHOTO)
            : okJson(201, { ...EVENT, photo_id: PHOTO.id, happened_on: today }),
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { onClose } = renderModal();

    const file = new File(["jpg"], "leaf.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByLabelText(/photo/i), {
      target: { files: [file] },
    });
    submit();

    await waitFor(() => {
      expect(onClose).toHaveBeenCalledTimes(1);
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);

    // Sequencing: the photo POST fires first, the event POST second.
    const [photoPath, photoInit] = fetchMock.mock.calls[0] as [
      string,
      RequestInit,
    ];
    expect(photoPath).toBe("/api/v1/plants/1/photos");
    expect(photoInit.body).toBeInstanceOf(FormData);

    const [eventPath, eventInit] = fetchMock.mock.calls[1] as [
      string,
      RequestInit,
    ];
    expect(eventPath).toBe("/api/v1/plants/1/events");
    const body = JSON.parse(eventInit.body as string) as Record<
      string,
      unknown
    >;
    expect(body).toEqual({
      type: "water",
      happened_on: today,
      photo_id: PHOTO.id,
    });
  });

  it("surfaces a photo-upload failure and never creates the event (F-14)", async () => {
    const fetchMock = vi.fn().mockResolvedValue(fail(415));
    vi.stubGlobal("fetch", fetchMock);
    const { onClose } = renderModal();

    const file = new File(["nope"], "doc.pdf", { type: "application/pdf" });
    fireEvent.change(screen.getByLabelText(/photo/i), {
      target: { files: [file] },
    });
    submit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toHaveTextContent(/photo/i);
    });
    // Only the photo POST fired; no orphan event without its intended photo.
    expect(fetchMock).toHaveBeenCalledTimes(1);
    expect((fetchMock.mock.calls[0] as [string])[0]).toBe(
      "/api/v1/plants/1/photos",
    );
    expect(onClose).not.toHaveBeenCalled();
  });

  it("surfaces an event-create failure after a successful upload (F-15)", async () => {
    const fetchMock = vi
      .fn()
      .mockImplementation((path: string) =>
        Promise.resolve(
          path.endsWith("/photos") ? okJson(201, PHOTO) : fail(422),
        ),
      );
    vi.stubGlobal("fetch", fetchMock);
    const { onClose } = renderModal();

    const file = new File(["jpg"], "leaf.jpg", { type: "image/jpeg" });
    fireEvent.change(screen.getByLabelText(/photo/i), {
      target: { files: [file] },
    });
    submit();

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(fetchMock).toHaveBeenCalledTimes(2);
    expect(onClose).not.toHaveBeenCalled();
  });
});
