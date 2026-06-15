import { afterEach, describe, expect, it, vi } from "vitest";

import { ApiError } from "./client";
import {
  getTimeline,
  type TimelineEntry,
  type TimelineEvent,
  type TimelinePhoto,
} from "./timeline";

// A discriminated feed carrying both arms: an event with an inline photo, an
// event with no photo, an observe with a health rating, and a standalone photo.
const SAMPLE_TIMELINE: TimelineEntry[] = [
  {
    kind: "photo",
    date: "2026-06-12",
    photo: { id: 11, url: "/api/v1/plants/1/photos/11" },
  },
  {
    kind: "event",
    date: "2026-06-11",
    event_type: "observe",
    note: "New leaf",
    health: "good",
    photo: { id: 12, url: "/api/v1/plants/1/photos/12" },
  },
  {
    kind: "event",
    date: "2026-06-10",
    event_type: "water",
    note: null,
    health: null,
    photo: null,
  },
];

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

function stubFetch(response: Response): ReturnType<typeof vi.fn> {
  const fetchMock = vi.fn().mockResolvedValue(response);
  vi.stubGlobal("fetch", fetchMock);
  return fetchMock;
}

describe("timeline API client", () => {
  afterEach(() => {
    vi.unstubAllGlobals();
    vi.restoreAllMocks();
  });

  it("GETs the timeline path with the JSON Accept header (F-1)", async () => {
    const fetchMock = stubFetch(okJson(200, SAMPLE_TIMELINE));

    await expect(getTimeline(1)).resolves.toEqual(SAMPLE_TIMELINE);

    expect(fetchMock).toHaveBeenCalledWith(
      "/api/v1/plants/1/timeline",
      expect.objectContaining({ headers: { Accept: "application/json" } }),
    );
  });

  it("maps the discriminated union correctly, narrowing on kind (F-2)", async () => {
    stubFetch(okJson(200, SAMPLE_TIMELINE));

    const feed = await getTimeline(1);

    // Narrowing on `kind` reads the right fields per arm (a consumer switching
    // on entry.kind type-checks and the compiler proves the access below).
    const events: TimelineEvent[] = [];
    const photos: TimelinePhoto[] = [];
    for (const entry of feed) {
      if (entry.kind === "event") {
        events.push(entry);
      } else {
        photos.push(entry);
      }
    }

    expect(events).toHaveLength(2);
    expect(photos).toHaveLength(1);

    const observe = events.find((e) => e.event_type === "observe");
    expect(observe?.health).toBe("good");
    expect(observe?.note).toBe("New leaf");
    expect(observe?.photo).toEqual({
      id: 12,
      url: "/api/v1/plants/1/photos/12",
    });

    const water = events.find((e) => e.event_type === "water");
    expect(water?.health).toBeNull();
    expect(water?.photo).toBeNull();

    expect(photos[0]?.photo).toEqual({
      id: 11,
      url: "/api/v1/plants/1/photos/11",
    });
  });

  it("throws ApiError on a non-2xx response (incl. 404) (F-3)", async () => {
    stubFetch(fail(404));
    await expect(getTimeline(99)).rejects.toBeInstanceOf(ApiError);
  });
});
