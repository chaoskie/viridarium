import { useState } from "react";
import { fireEvent, render, screen, waitFor } from "@testing-library/react";
import { afterEach, describe, expect, it, vi } from "vitest";

import type { Plant } from "@/lib/api/plants";

import type { DueCareType } from "./buildTodayGroups";
import { TodayCard, type TodayCardModel } from "./TodayCard";

/** Today's local calendar date as YYYY-MM-DD (independent oracle). */
function localToday(): string {
  const now = new Date();
  const month = String(now.getMonth() + 1).padStart(2, "0");
  const day = String(now.getDate()).padStart(2, "0");
  return `${String(now.getFullYear())}-${month}-${day}`;
}

function _plant(id: number, name: string): Plant {
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

function due(
  care_type: "water" | "feed",
  overdue_days: number,
  next_due: string,
): DueCareType {
  return { care_type, overdue_days, next_due };
}

function model(plant: Plant, dueCareTypes: DueCareType[]): TodayCardModel {
  const worstOverdue = Math.max(0, ...dueCareTypes.map((d) => d.overdue_days));
  return { plant, dueCareTypes, worstOverdue };
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

function createdEvent(type: "water" | "feed"): unknown {
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

/** Harness that removes the card when it reports all care satisfied (C-14). */
function CardHarness({
  initial,
}: {
  readonly initial: TodayCardModel;
}): JSX.Element {
  const [present, setPresent] = useState(true);
  if (!present) {
    return <div data-testid="empty-list" />;
  }
  return (
    <TodayCard
      card={initial}
      onAllCareLogged={() => {
        setPresent(false);
      }}
    />
  );
}

afterEach(() => {
  vi.unstubAllGlobals();
  vi.restoreAllMocks();
});

describe("TodayCard", () => {
  it("C-8 button set: Water iff water due, Feed iff feed due", () => {
    const waterOnly = model(_plant(1, "Aloe"), [due("water", 1, localToday())]);
    const { unmount } = render(
      <ul>
        <TodayCard card={waterOnly} />
      </ul>,
    );
    expect(screen.getByRole("button", { name: /^Water/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^Feed/i }),
    ).not.toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^Both/i }),
    ).not.toBeInTheDocument();
    unmount();

    const feedOnly = model(_plant(1, "Aloe"), [due("feed", 0, localToday())]);
    render(
      <ul>
        <TodayCard card={feedOnly} />
      </ul>,
    );
    expect(screen.getByRole("button", { name: /^Feed/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^Water/i }),
    ).not.toBeInTheDocument();
  });

  it("C-9 Both button appears ONLY when both due (CRITICAL)", () => {
    const both = model(_plant(1, "Pothos"), [
      due("water", 2, localToday()),
      due("feed", 0, localToday()),
    ]);
    const { unmount } = render(
      <ul>
        <TodayCard card={both} />
      </ul>,
    );
    expect(screen.getByRole("button", { name: /^Water/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Feed/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Both/i })).toBeInTheDocument();
    unmount();

    const single = model(_plant(1, "Pothos"), [due("water", 1, localToday())]);
    render(
      <ul>
        <TodayCard card={single} />
      </ul>,
    );
    expect(
      screen.queryByRole("button", { name: /^Both/i }),
    ).not.toBeInTheDocument();
  });

  it("C-10 tapping Water logs water for today", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("water")));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Aloe"), [due("water", 1, localToday())])}
        />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Water/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    const [path, init] = fetchMock.mock.calls[0] as [string, RequestInit];
    expect(path).toBe("/api/v1/plants/1/events");
    expect(init.method).toBe("POST");
    expect(JSON.parse(init.body as string)).toEqual({
      type: "water",
      happened_on: localToday(),
    });
  });

  it("C-11 tapping Feed logs feed for today", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("feed")));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Aloe"), [due("feed", 0, localToday())])}
        />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Feed/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(1);
    });
    expect(
      JSON.parse(
        (fetchMock.mock.calls[0] as [string, RequestInit])[1].body as string,
      ),
    ).toEqual({ type: "feed", happened_on: localToday() });
  });

  it("C-12 tapping Both logs BOTH types for today (CRITICAL)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(201, createdEvent("water")))
      .mockResolvedValueOnce(okJson(201, createdEvent("feed")));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Pothos"), [
            due("water", 2, localToday()),
            due("feed", 0, localToday()),
          ])}
        />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Both/i }));

    await waitFor(() => {
      expect(fetchMock).toHaveBeenCalledTimes(2);
    });
    const bodies = fetchMock.mock.calls.map(
      (c) =>
        JSON.parse((c as [string, RequestInit])[1].body as string) as {
          type: string;
          happened_on: string;
        },
    );
    const types = bodies.map((b) => b.type).sort();
    expect(types).toEqual(["feed", "water"]);
    bodies.forEach((b) => {
      expect(b.happened_on).toBe(localToday());
    });
  });

  it("C-13 card updates WITHOUT reload: the satisfied type drops, card stays (CRITICAL)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("water")));
    vi.stubGlobal("fetch", fetchMock);
    const both = model(_plant(1, "Pothos"), [
      due("water", 2, localToday()),
      due("feed", 0, localToday()),
    ]);
    render(
      <ul>
        <CardHarness initial={both} />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Water/i }));

    await waitFor(() => {
      expect(
        screen.queryByRole("button", { name: /^Water/i }),
      ).not.toBeInTheDocument();
    });
    // Feed remains; the Both button is gone (only one type left); card stays.
    expect(screen.getByRole("button", { name: /^Feed/i })).toBeInTheDocument();
    expect(
      screen.queryByRole("button", { name: /^Both/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByText("Pothos")).toBeInTheDocument();
    expect(screen.queryByTestId("empty-list")).not.toBeInTheDocument();
  });

  it("C-14 card LEAVES the list when nothing is left due (CRITICAL)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValue(okJson(201, createdEvent("water")));
    vi.stubGlobal("fetch", fetchMock);
    const waterOnly = model(_plant(1, "Aloe"), [due("water", 1, localToday())]);
    render(
      <ul>
        <CardHarness initial={waterOnly} />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Water/i }));

    await waitFor(() => {
      expect(screen.getByTestId("empty-list")).toBeInTheDocument();
    });
    expect(screen.queryByText("Aloe")).not.toBeInTheDocument();
  });

  it("C-15 a failed log surfaces inline; the card and care type stay", async () => {
    vi.stubGlobal("fetch", vi.fn().mockResolvedValue(fail(500)));
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Aloe"), [due("water", 1, localToday())])}
        />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Water/i }));

    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(screen.getByRole("button", { name: /^Water/i })).toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Water/i })).toBeEnabled();
  });

  it("C-16 buttons disabled in-flight, re-enabled after settle", async () => {
    let resolve: (r: Response) => void = () => undefined;
    const pending = new Promise<Response>((r) => {
      resolve = r;
    });
    vi.stubGlobal(
      "fetch",
      vi.fn(() => pending),
    );
    // Both due so a sibling button survives the tap and can show the re-enable.
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Pothos"), [
            due("water", 2, localToday()),
            due("feed", 0, localToday()),
          ])}
        />
      </ul>,
    );

    const water = screen.getByRole("button", { name: /^Water/i });
    const feed = screen.getByRole("button", { name: /^Feed/i });
    fireEvent.click(water);

    // In-flight: both buttons disable while the request is pending.
    await waitFor(() => {
      expect(water).toBeDisabled();
    });
    expect(feed).toBeDisabled();

    // Settle the in-flight request and wait for the resulting state update
    // inside the test lifecycle, so the re-enable happens within act() (no
    // dangling-update warning). Water drops (logged); the surviving Feed button
    // re-enables.
    resolve(okJson(201, createdEvent("water")));
    await waitFor(() => {
      expect(feed).not.toBeDisabled();
    });
    expect(
      screen.queryByRole("button", { name: /^Water/i }),
    ).not.toBeInTheDocument();
  });

  it("C-17 partial Both failure drops only the succeeded type (no duplicate)", async () => {
    const fetchMock = vi
      .fn()
      .mockResolvedValueOnce(okJson(201, createdEvent("water")))
      .mockResolvedValueOnce(fail(500));
    vi.stubGlobal("fetch", fetchMock);
    render(
      <ul>
        <TodayCard
          card={model(_plant(1, "Pothos"), [
            due("water", 2, localToday()),
            due("feed", 0, localToday()),
          ])}
        />
      </ul>,
    );

    fireEvent.click(screen.getByRole("button", { name: /^Both/i }));

    // Error surfaces; water (succeeded) drops so a re-tap cannot duplicate it;
    // feed (genuinely still due) remains.
    await waitFor(() => {
      expect(screen.getByRole("alert")).toBeInTheDocument();
    });
    expect(
      screen.queryByRole("button", { name: /^Water/i }),
    ).not.toBeInTheDocument();
    expect(screen.getByRole("button", { name: /^Feed/i })).toBeInTheDocument();

    // createEvent called for water then feed, in that order.
    expect(fetchMock).toHaveBeenCalledTimes(2);
    const sentTypes = fetchMock.mock.calls.map(
      (c) =>
        (
          JSON.parse((c as [string, RequestInit])[1].body as string) as {
            type: string;
          }
        ).type,
    );
    expect(sentTypes).toEqual(["water", "feed"]);
  });
});
