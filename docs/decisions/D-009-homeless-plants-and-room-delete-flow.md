# D-009: Homeless plants and the room-delete flow

Status: ratified, 2026-06-08. Refines [product-spec](../product-spec.md) section 3.

## Context

Location CRUD (US-2.2) was built before Plant CRUD (US-2.1). Its acceptance criterion
"delete only when empty or with reassignment" had nothing to act on yet, which raised the
broader question of what a plant without a location means.

## Decision

1. **A plant may have no location ("homeless") as a deliberate, first-class state**, not
   only as a side effect of deleting a room. Motivating case: a plant dies, but its
   history and photos are kept for reference and should not occupy a real room.
   `Plant.location` is therefore optional (nullable).
2. **Room-delete flow:**
   - A room with no plants is deleted immediately.
   - A room with plants prompts "what do you want to do with the plants?":
     - **A. Delete them:** room and plants are deleted.
     - **B. Move them:** pick an existing room or create one inline; plants move, the old
       room is deleted.
     - **C. Decide later:** the room is deleted and its plants become homeless.
3. **Sequencing:** US-2.2 shipped plain Location CRUD. US-2.1 introduced `Plant` with an
   optional location. Bulk location management (multi-select move, move out of homeless)
   is a follow-up on the [roadmap](../roadmap.md).

## Options considered

- **Chosen:** plain delete first, full flow with the Plant story. Keeps the first slice
  thin and avoids building reassignment machinery against an entity that did not exist.
- Build a plant-counter port returning 0 until plants exist. Rejected: infrastructure for
  a collaborator that does not exist yet.
- Require a location and forbid deleting non-empty rooms. Rejected: the homeless state is
  wanted regardless of deletion.

## Rationale

Homeless is a real product need, not a deletion edge case. "The user always wins the
argument with the algorithm" (product-spec section 3) extends here: the user decides what
happens to plants, and the app never strands or silently deletes them.

## Consequences

- `Plant.location` is optional in the domain model, ORM, schemas and migration.
- The UI needs a place to see and triage homeless plants.
- Homeless is orthogonal to archived: a plant can be homeless without being archived.

## Implemented baseline

`plant.location_id` is a nullable foreign key with `ON DELETE SET NULL`: deleting a room
makes its plants homeless (option C), the safe default that never deletes history. The
A/B/C prompt and bulk move build on top of that.

SQLite only honors foreign-key delete actions with `PRAGMA foreign_keys=ON` per
connection. The engine setup sets that pragma, and a dual-engine test
(`backend/tests/integration/test_fk_cross_engine.py`) asserts that a plant goes homeless,
not dangling and not deleted, when its room is removed.
