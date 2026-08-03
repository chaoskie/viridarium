import { describe, expect, it } from "vitest";

import type { Location } from "@/lib/api/locations";
import type { Plant, ScheduleDue } from "@/lib/api/plants";

import { buildTodayGroups } from "./buildTodayGroups";

// Fixed injected "today" - every next_due is computed relative to it so the
// suite never reads a real clock (TEST-006).
const TODAY = "2026-06-15";

/** Build a YYYY-MM-DD `offsetDays` away from TODAY (negative = past). */
function dateOffset(offsetDays: number): string {
  const base = new Date(`${TODAY}T00:00:00Z`);
  base.setUTCDate(base.getUTCDate() + offsetDays);
  return base.toISOString().slice(0, 10);
}

function _schedule(
  care_type: "water" | "feed",
  next_due: string | null,
  overdue_days: number | null,
): ScheduleDue {
  return { care_type, next_due, overdue_days };
}

function _plant(
  id: number,
  name: string,
  location_id: number | null,
  schedules: readonly ScheduleDue[],
): Plant {
  return {
    id,
    name,
    species: null,
    location_id,
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
    schedules,
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  };
}

function _location(id: number, name: string): Location {
  return {
    id,
    name,
    notes: null,
    created_at: "2026-06-08T10:00:00Z",
    updated_at: "2026-06-08T10:00:00Z",
  };
}

/** Flatten all cards across groups for assertions that span groups. */
function allCards(
  groups: ReturnType<typeof buildTodayGroups>,
): { plant: Plant; dueCareTypes: readonly { care_type: string }[] }[] {
  return groups.flatMap((g) => g.cards);
}

function cardFor(
  groups: ReturnType<typeof buildTodayGroups>,
  plantId: number,
): (typeof groups)[number]["cards"][number] | undefined {
  return allCards(groups).find((c) => c.plant.id === plantId) as
    (typeof groups)[number]["cards"][number] | undefined;
}

describe("buildTodayGroups - classification + exclusion (M-CLS, AC1/AC2/AC4)", () => {
  // U-1: the M-CLS matrix, one plant per row (each in its own named location so
  // a surviving row produces exactly one card).
  const CLS_ROWS: {
    id: string;
    next_due: string | null;
    overdue_days: number | null;
    care_type: "water" | "feed";
    inCard: boolean;
  }[] = [
    {
      id: "overdue-water",
      next_due: dateOffset(-3),
      overdue_days: 3,
      care_type: "water",
      inCard: true,
    },
    {
      id: "overdue-feed",
      next_due: dateOffset(-1),
      overdue_days: 1,
      care_type: "feed",
      inCard: true,
    },
    {
      id: "due-today-water",
      next_due: TODAY,
      overdue_days: 0,
      care_type: "water",
      inCard: true,
    },
    {
      id: "due-today-feed",
      next_due: TODAY,
      overdue_days: 0,
      care_type: "feed",
      inCard: true,
    },
    {
      id: "future-water",
      next_due: dateOffset(5),
      overdue_days: 0,
      care_type: "water",
      inCard: false,
    },
    {
      id: "future-feed",
      next_due: dateOffset(2),
      overdue_days: 0,
      care_type: "feed",
      inCard: false,
    },
    {
      id: "paused-water",
      next_due: null,
      overdue_days: null,
      care_type: "water",
      inCard: false,
    },
    {
      id: "paused-feed",
      next_due: null,
      overdue_days: null,
      care_type: "feed",
      inCard: false,
    },
  ];

  it.each(CLS_ROWS)(
    "U-1 classifies/excludes the $id row",
    ({ next_due, overdue_days, care_type, inCard }) => {
      const plant = _plant(1, "Subject", 1, [
        _schedule(care_type, next_due, overdue_days),
      ]);
      const groups = buildTodayGroups(
        [plant],
        [_location(1, "Kitchen")],
        TODAY,
      );
      const card = cardFor(groups, 1);

      if (inCard) {
        expect(card).toBeDefined();
        expect(card?.dueCareTypes.map((d) => d.care_type)).toEqual([care_type]);
        if ((overdue_days ?? 0) > 0) {
          expect(card?.worstOverdue).toBe(overdue_days);
        } else {
          expect(card?.worstOverdue).toBe(0);
        }
      } else {
        // Excluded rows leave the plant entirely absent (no phantom card).
        expect(card).toBeUndefined();
        expect(allCards(groups)).toHaveLength(0);
      }
    },
  );
});

describe("buildTodayGroups - plant-level fan-out (M-CLS 3a, AC2/AC3/AC4)", () => {
  it("U-2 both-due yields BOTH care types (CRITICAL, the Both-button driver)", () => {
    const plant = _plant(1, "Monstera", 1, [
      _schedule("water", dateOffset(-2), 2),
      _schedule("feed", TODAY, 0),
    ]);
    const card = cardFor(
      buildTodayGroups([plant], [_location(1, "Kitchen")], TODAY),
      1,
    );
    const types = card?.dueCareTypes.map((d) => d.care_type).sort();
    expect(types).toEqual(["feed", "water"]);
    expect(card?.worstOverdue).toBe(2);
  });

  it("U-3 water-only excludes the future feed", () => {
    const plant = _plant(1, "Aloe", 1, [
      _schedule("water", dateOffset(-1), 1),
      _schedule("feed", dateOffset(3), 0),
    ]);
    const card = cardFor(
      buildTodayGroups([plant], [_location(1, "Kitchen")], TODAY),
      1,
    );
    expect(card?.dueCareTypes.map((d) => d.care_type)).toEqual(["water"]);
  });

  it("U-4 feed-only excludes the paused water", () => {
    const plant = _plant(1, "Yarrow", 1, [
      _schedule("water", null, null),
      _schedule("feed", TODAY, 0),
    ]);
    const card = cardFor(
      buildTodayGroups([plant], [_location(1, "Kitchen")], TODAY),
      1,
    );
    expect(card?.dueCareTypes.map((d) => d.care_type)).toEqual(["feed"]);
  });

  it("U-5 worstOverdue == max(overdue_days)", () => {
    const plant = _plant(1, "Fern", 1, [
      _schedule("water", dateOffset(-5), 5),
      _schedule("feed", dateOffset(-1), 1),
    ]);
    const card = cardFor(
      buildTodayGroups([plant], [_location(1, "Kitchen")], TODAY),
      1,
    );
    expect(card?.worstOverdue).toBe(5);
    expect(card?.dueCareTypes.map((d) => d.care_type).sort()).toEqual([
      "feed",
      "water",
    ]);
  });

  it("U-6 a plant with no due schedule is absent (CRITICAL)", () => {
    const plant = _plant(1, "Cactus", 1, [
      _schedule("water", dateOffset(1), 0),
      _schedule("feed", null, null),
    ]);
    const groups = buildTodayGroups([plant], [_location(1, "Kitchen")], TODAY);
    expect(allCards(groups)).toHaveLength(0);
  });

  it("U-7 empty input -> no groups", () => {
    expect(buildTodayGroups([], [], TODAY)).toEqual([]);
  });
});

describe("buildTodayGroups - grouping + ordering (M-GRP 3b, AC1, CRITICAL)", () => {
  it("U-8 groups by location + the homeless 'No location' group", () => {
    const plants = [
      _plant(1, "Kitchen Plant", 2, [_schedule("water", TODAY, 0)]),
      _plant(2, "Homeless Plant", null, [_schedule("water", TODAY, 0)]),
    ];
    const groups = buildTodayGroups(plants, [_location(2, "Kitchen")], TODAY);
    const names = groups.map((g) => g.locationName);
    expect(names).toContain("Kitchen");
    expect(names).toContain("No location");
    const homeless = groups.find((g) => g.locationName === "No location");
    expect(homeless?.cards.map((c) => c.plant.id)).toEqual([2]);
    const kitchen = groups.find((g) => g.locationName === "Kitchen");
    expect(kitchen?.cards.map((c) => c.plant.id)).toEqual([1]);
  });

  it("U-9 groups order by location name, homeless LAST (CRITICAL)", () => {
    const plants = [
      _plant(1, "P-Zen", 3, [_schedule("water", TODAY, 0)]),
      _plant(2, "P-Atrium", 1, [_schedule("water", TODAY, 0)]),
      _plant(3, "P-Kitchen", 2, [_schedule("water", TODAY, 0)]),
      _plant(4, "P-Homeless", null, [_schedule("water", TODAY, 0)]),
    ];
    const locations = [
      _location(1, "Atrium"),
      _location(2, "Kitchen"),
      _location(3, "Zen room"),
    ];
    const groups = buildTodayGroups(plants, locations, TODAY);
    expect(groups.map((g) => g.locationName)).toEqual([
      "Atrium",
      "Kitchen",
      "Zen room",
      "No location",
    ]);
  });

  it("U-10 within-group most-overdue-first then name", () => {
    const plants = [
      _plant(1, "Plant A", 1, [_schedule("water", dateOffset(-1), 1)]),
      _plant(2, "Plant B", 1, [_schedule("water", dateOffset(-4), 4)]),
      _plant(3, "Yarrow", 1, [_schedule("feed", dateOffset(-2), 2)]),
      _plant(4, "Aloe", 1, [_schedule("feed", dateOffset(-2), 2)]),
    ];
    const groups = buildTodayGroups(plants, [_location(1, "Kitchen")], TODAY);
    expect(groups).toHaveLength(1);
    // B(4) first, then the two od-2 plants name-asc (Aloe, Yarrow), then A(1).
    expect(groups[0]?.cards.map((c) => c.plant.name)).toEqual([
      "Plant B",
      "Aloe",
      "Yarrow",
      "Plant A",
    ]);
  });

  it("U-11 resolves location name from locations; unresolved id -> No location", () => {
    const plants = [
      _plant(1, "Greenhouse Plant", 7, [_schedule("water", TODAY, 0)]),
      _plant(2, "Orphan Plant", 99, [_schedule("water", TODAY, 0)]),
    ];
    const groups = buildTodayGroups(
      plants,
      [_location(7, "Greenhouse")],
      TODAY,
    );
    const names = groups.map((g) => g.locationName);
    expect(names).toContain("Greenhouse");
    const greenhouse = groups.find((g) => g.locationName === "Greenhouse");
    expect(greenhouse?.cards.map((c) => c.plant.id)).toEqual([1]);
    // The unresolved id falls into the homeless group (defensive default).
    const homeless = groups.find((g) => g.locationName === "No location");
    expect(homeless?.cards.map((c) => c.plant.id)).toEqual([2]);
  });
});
