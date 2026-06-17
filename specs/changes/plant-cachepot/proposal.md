# Proposal - plant-cachepot (US-2.x, from 2026-06-17 S25+ soak feedback #5)

Status: proposed.

## Story (SPEC-004)

As a plant owner, I want to record that a plant's nursery (inner) pot sits inside a
decorative outer pot (cachepot) - including the outer pot's material and optional
size - so that the app captures the watering-relevant pot setup and can later guide
cachepot care (e.g. bottom-watering: lift the inner pot out, soak it ~10 min, let it
drain in the sink).

## Problem

Today a `Plant` has a single `pot_material` (`PotMaterial` enum) + `pot_size_cm`. Many
houseplants live in a **plastic nursery (inner) pot** standing inside a **decorative
outer pot / cachepot**. The model can't express that combination, yet it is exactly
the watering-relevant fact: the inner pot governs drainage and how fast soil dries,
while the outer is decorative and can silently waterlog the plant. Knowing the pairing
exists is what later lets us suggest bottom-watering and "don't let water pool in the
cachepot" care.

## Scope (exact, PRIN-IX)

Descriptive data only in v1 - **no care/schedule logic yet** (that is the follow-up
phase the data unlocks). Additive and non-breaking.

- **Domain:** new `OuterPotMaterial` `StrEnum`; add `outer_pot_material: OuterPotMaterial | None`
  and `outer_pot_size_cm: int | None` to the plant entity. The existing
  `pot_material` / `pot_size_cm` are **kept as-is** and semantically denote the
  inner/nursery pot (documented; not renamed - renaming is a breaking API change).
- **Persistence:** one migration adding two nullable columns (`outer_pot_material`
  `String(20)`, `outer_pot_size_cm` `Integer`) to the plant table; dual-engine
  (SQLite batch + PostgreSQL), reversible.
- **Web/contract:** add the two optional fields to `PlantCreate` / `PlantUpdate` /
  `PlantResponse`. Additive optional fields → non-breaking (API-001; API-004 not
  triggered).
- **Frontend:** add `outer_pot_material` + `outer_pot_size_cm` to the plants API
  client and an "Outer / decorative pot" section in `PlantFormModal`; relabel the
  existing pot fields to "Nursery (inner) pot" for clarity (UI label only, no API
  change). Display is optional/minimal on the list/detail.

## Out of scope

- Any watering/schedule/due logic or waterlogging warnings (future phase - the data
  here is the enabler).
- Renaming or restructuring the existing pot fields; no separate pots table/object.
- Validating the inner-vs-outer size relationship (outer usually ≥ inner) - deferred.
- Backfilling/guessing outer pots for existing plants (they stay null = "no cachepot").

## Acceptance criteria

- AC1: `POST/PUT /api/v1/plants` accepts `outer_pot_material` (valid `OuterPotMaterial`
  or null) and `outer_pot_size_cm` (1-500 or null); invalid enum / out-of-range → 422.
- AC2: `PlantResponse` returns both new fields; a plant created without them reads back
  `null` for both (existing single-pot plants unaffected).
- AC3: the migration applies and reverses cleanly on **both** SQLite and PostgreSQL
  (ARCH-011); existing plant rows get `NULL` for the new columns.
- AC4: the add/edit plant form can set and clear the outer pot material + size; the
  inner-pot fields are relabelled "Nursery (inner) pot".
- AC5: all existing plant tests stay green; no contract break (existing clients keep working).

## Dependencies

- Touches the same files as the (now-merged) plant-crud surface; no blocking
  dependency. Independent of the `botanicum` species-defaults change. No upstream work.

## Logging / security (SEC)

No new sensitive data (pot material/size is non-PII); no trust-boundary or CORS impact
(SEC-001); no new logging events required (SEC-008). No auth change (SEC-003).

## Architecture (ARCH)

Fits the hexagon unchanged: enum + fields in `domain`, columns in `adapters/outbound/db`,
schema in `adapters/inbound/web`. Enum stored as `String(20)` per D3 precedent (no native
DB enum, ARCH-011). No stack amendment (ARCH-001 / PRIN-V).

## Estimate + responsibilities

~150-250 LOC across two disjoint lanes (backend + frontend), 1 day. Well under the
~400-500 LOC budget; single story, no split. test-engineer authors the test-foundation
(G0); backend + frontend agents implement; reviewer gate + DoD to close.

## Contract impact (API-001)

Additive optional fields on the `plants` schemas. OpenAPI delta: `PlantCreate`,
`PlantUpdate`, `PlantResponse` each gain `outer_pot_material` (string enum, nullable)
and `outer_pot_size_cm` (integer 1-500, nullable). Non-breaking; API-004 not triggered.

## Assumptions (non-scope unknowns, proceeding as stated)

- `OuterPotMaterial` values: `ceramic`, `terracotta`, `plastic`, `metal`, `woven`,
  `glass`, `other` (decorative set; no `self-watering`, which is an inner-pot trait).
  Refinable in `design.md`.
- `outer_pot_size_cm` reuses the inner bound (integer 1-500).
- Inner pot = the existing `pot_material`/`pot_size_cm`; UI relabels to "Nursery (inner)
  pot", API names unchanged.

Open questions: none. (Scope-affecting questions - care impact, model shape, outer-pot
detail - were asked and answered by the maintainer 2026-06-17; recorded above.)

## DoR: see worklog for the posted PASS/WATCH/FAIL checklist.
