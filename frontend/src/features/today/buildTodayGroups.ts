import type { Location } from "@/lib/api/locations";
import type { Plant, ScheduleDue } from "@/lib/api/plants";

/** The "No location" homeless group label (D-009). */
export const NO_LOCATION_LABEL = "No location";

/**
 * One due care type on a card: the schedule's `care_type` plus the resolved,
 * non-null `next_due`/`overdue_days` (a schedule reaches a card only when both
 * are non-null - it is due or overdue).
 */
export interface DueCareType {
  readonly care_type: "water" | "feed";
  readonly overdue_days: number;
  readonly next_due: string;
}

/** One plant's Today card: the plant, its due care types, and the worst overdue. */
export interface TodayCardModel {
  readonly plant: Plant;
  readonly dueCareTypes: readonly DueCareType[];
  /** `max(overdue_days)` across `dueCareTypes`; 0 when only due-today. */
  readonly worstOverdue: number;
}

/** A location group of cards, in render order. */
export interface TodayGroup {
  readonly locationName: string;
  readonly cards: readonly TodayCardModel[];
}

/**
 * A schedule needs attention iff it is enabled (`next_due != null`) AND due
 * today or earlier (`next_due <= today`). A future schedule (`next_due > today`)
 * and a paused/dormant one (`next_due == null`) are excluded. `overdue_days` is
 * null iff `next_due` is null, so a surviving schedule always carries a number.
 */
function dueCareTypeOf(
  schedule: ScheduleDue,
  today: string,
): DueCareType | null {
  if (schedule.next_due === null) {
    return null;
  }
  if (schedule.next_due > today) {
    return null;
  }
  return {
    care_type: schedule.care_type,
    // overdue_days is non-null whenever next_due is non-null (both-null
    // invariant, US-3.3); clamp defensively to a number.
    overdue_days: schedule.overdue_days ?? 0,
    next_due: schedule.next_due,
  };
}

/** Build a card for one plant, or null when it has no due schedule. */
function cardOf(plant: Plant, today: string): TodayCardModel | null {
  const dueCareTypes: DueCareType[] = [];
  for (const schedule of plant.schedules) {
    const due = dueCareTypeOf(schedule, today);
    if (due !== null) {
      dueCareTypes.push(due);
    }
  }
  if (dueCareTypes.length === 0) {
    return null;
  }
  const worstOverdue = Math.max(...dueCareTypes.map((d) => d.overdue_days));
  return { plant, dueCareTypes, worstOverdue };
}

/** Sort cards within a group: worstOverdue desc, then plant name asc. */
function compareCards(a: TodayCardModel, b: TodayCardModel): number {
  if (a.worstOverdue !== b.worstOverdue) {
    return b.worstOverdue - a.worstOverdue;
  }
  return a.plant.name.localeCompare(b.plant.name);
}

/**
 * The pure Today-view derivation (design §"The pure derivation"): from the
 * plants (each carrying its `schedules` due state) plus the locations (for
 * names) and the injected `today` (YYYY-MM-DD, no clock read here), produce the
 * ordered location groups of cards.
 *
 * - Each plant's schedules are filtered to the due/overdue set; a plant with
 *   none produces no card (AC4).
 * - Cards group by `location_id`; a null (or unresolved) location id falls into
 *   the "No location" group (D-009).
 * - Groups order by location name asc, the homeless group LAST regardless of
 *   label; within a group cards sort worstOverdue desc then plant name (AC1).
 */
export function buildTodayGroups(
  plants: readonly Plant[],
  locations: readonly Location[],
  today: string,
): TodayGroup[] {
  const nameById = new Map<number, string>();
  for (const loc of locations) {
    nameById.set(loc.id, loc.name);
  }

  // Group cards by resolved location name; homeless collected separately.
  const namedGroups = new Map<string, TodayCardModel[]>();
  const homeless: TodayCardModel[] = [];

  for (const plant of plants) {
    const card = cardOf(plant, today);
    if (card === null) {
      continue;
    }
    const name =
      plant.location_id !== null ? nameById.get(plant.location_id) : undefined;
    if (name === undefined) {
      homeless.push(card);
    } else {
      const bucket = namedGroups.get(name) ?? [];
      bucket.push(card);
      namedGroups.set(name, bucket);
    }
  }

  const groups: TodayGroup[] = [...namedGroups.entries()]
    .sort((a, b) => a[0].localeCompare(b[0]))
    .map(([locationName, cards]) => ({
      locationName,
      cards: [...cards].sort(compareCards),
    }));

  if (homeless.length > 0) {
    groups.push({
      locationName: NO_LOCATION_LABEL,
      cards: [...homeless].sort(compareCards),
    });
  }

  return groups;
}
