# Proposal - species-catalog (Botanicum Phase 1A; from 2026-06-17 soak feedback #6)

Status: proposed.

## Story (SPEC-004)

As a plant owner, I want a built-in catalog of common houseplant species with their
basic care defaults (light, watering, feeding, winter behaviour), so that I can later
pick a species for my plant and have its care pre-filled instead of guessing every value.

This change delivers the **catalog itself** (data + read API). The pick-to-prefill
integration on the plant form is the immediate follow-up story (see "Epic & split").

## Problem

`species` on a plant is free text today, and every care value (light, watering/feeding
intervals, dormancy) is set by hand per plant. New users have nothing to anchor on. A
curated "botanicum" of common species with sensible defaults turns a blank form into a
guided start, while still letting each plant override.

## Botanicum epic & phased split

"Botanicum" is an epic; v1 is intentionally narrow. Proposed split (PRIN-VI / SPEC-004,
since the whole epic far exceeds the ~400-500 LOC budget):

- **Phase 1A - species-catalog (THIS change):** species table + curated seed +
  read-only catalog API. Backend-only; no plant changes. Independently shippable.
- **Phase 1B - plant-species-prefill (next proposal):** add nullable `species_id` to
  plant (provenance record), a species picker in the plant form, and prefill of
  light + watering/feeding/winter from the chosen species into the plant's own
  editable fields (**prefill & detach** - values are copied, the link is kept only as
  a record). Depends on 1A.
- **Phase 2 - editable catalog:** let the user add/adjust species (CRUD) and expand
  categories/coverage over time.
- **Phase 3 - care guidance & richer dimensions:** the deeper wishlist below, plus a
  future "a species default changed - update N linked plants?" prompt (with an alert
  that it may override per-plant customisations).

## Scope of THIS change (Phase 1A, exact - PRIN-IX)

- **Domain:** `Species` entity + `SpeciesRepository` (read-only port). A species
  carries: `slug`/`id`, `common_name`, `scientific_name` (opt), `category` (opt, e.g.
  cactus-succulent, foliage, fern), and the four v1 defaults:
  `light_level` (existing `LightLevel` enum), `water_interval_days`,
  `feed_interval_days`, `winter_interval_days` (opt), `dormancy` (existing `Dormancy`
  enum). All default fields optional (a category-level entry may omit specifics).
- **Persistence:** `species` table + a curated **seed of ~25-30 common houseplants**
  (incl. broad-behaviour category entries like "cacti & succulents"), loaded via a
  data-seeding migration; dual-engine (SQLite + PostgreSQL), reversible.
- **Web/contract:** read-only `GET /api/v1/species` (list, optional `?category=` and
  `?q=` filters) and `GET /api/v1/species/{id}`. New `species` OpenAPI tag.
- **No frontend in 1A** beyond the typed API client (`lib/api/species.ts`); the picker
  UI lands in 1B.

## Out of scope (this change)

- Any plant change (`species_id` FK, the picker, prefill) - that is Phase 1B.
- Catalog editing / user-authored species (Phase 2).
- All Phase-3 dimensions in the roadmap below (captured, not built).
- The unresolved "non-interval watering" modelling (see roadmap challenges).

## Acceptance criteria

- AC1: `GET /api/v1/species` returns the seeded catalog (each item: identity +
  category + the four defaults, defaults nullable); `?category=` and `?q=` filter it.
- AC2: `GET /api/v1/species/{id}` returns one species; unknown id → 404.
- AC3: the seed loads via migration on **both** SQLite and PostgreSQL (ARCH-011) and
  reverses cleanly; the catalog is identical across engines.
- AC4: the catalog is read-only over the API in 1A (no POST/PUT/DELETE surface yet).
- AC5: existing plant behaviour is completely unchanged (no plant schema touch).

## Roadmap - future botanicum dimensions (captured from maintainer, NOT in v1)

Per-species information to cover as the catalog deepens (Phase 2/3). Several carry
open modelling challenges flagged for later design:

- **Potting mix preference** - organic vs mineral/grit (e.g. cacti).
- **Feeding** - fertiliser type + amount + period (richer than a single interval).
- **Watering as a *mode*, not just an interval** - e.g. "wet feet / keep moist",
  "never let dry out", "top ~5 cm may feel dry", "let dry between", "prefer too dry /
  sparse". *Challenge:* many plants aren't watered on a fixed periodic interval -
  research how other apps model "water when the top N cm is dry" vs a day cadence.
- **Humidity** - likes humid air → mist every N days.
- **Seasonality unit** - winter care is often expressed in **weeks, not days**; resolve
  the interval-unit modelling.
- **Light intensity preference** (richer than the 4-level enum).
- **Repotting** - some species prefer a **rootbound** state over a bigger pot.
- **Edible / toxic** to humans & pets.
- **Flowers** - bloom care / how to optimise flowering.
- **Pruning** guidance.
- **Growth rate / habit.**
- **Categories** - group species that behave alike (cacti & succulents), with
  variety-level detail layered in later.

## Dependencies

- None upstream. Phase 1B depends on this. Independent of `plant-cachepot`.

## Logging / security (SEC)

Catalog data is public, non-PII reference content; no secrets, no trust-boundary
change (SEC-001), no auth (SEC-003). Read-only API → no write-abuse surface. No special
logging (SEC-008).

## Architecture (ARCH)

New read-only bounded slice in the hexagon: `domain` (Species + port), `application`
(read service), `adapters/inbound/web` (router), `adapters/outbound/db` (model +
seed migration). Enums stored as `String(20)` (D3 precedent, ARCH-011). Seed shipped as
repo data loaded by migration so it is identical and offline on both engines. No stack
amendment (ARCH-001 / PRIN-V).

## Estimate + responsibilities

~400-500 LOC incl. seed data (mostly content, low logic), ~1-2 days. At the budget
ceiling for one story - the plant integration is deliberately split into 1B to stay
within it. test-engineer authors G0; backend agent implements; reviewer + DoD to close.

## Contract impact (API-001)

Net-new read-only `species` paths; purely additive (no change to existing surfaces).
OpenAPI gains `Species` schema + the two GET paths. Non-breaking; API-004 not triggered.
The codegen-output assertion (TEST-008) is extended for the new paths/schema.

## Assumptions (non-scope unknowns, proceeding as stated)

- Seed list is a curated ~25-30 starter set chosen by the maintainer; exact species
  finalised during G0/implementation (content, not contract).
- `category` is a free-ish small enum/string (e.g. `cactus-succulent`, `foliage`,
  `fern`, `palm`, `flowering`, `other`); refinable in design.
- v1 defaults reuse existing `LightLevel` and `Dormancy` enums and day-based intervals
  (the weeks-vs-days seasonality question is a roadmap item, not v1).
- Species identified by a stable `slug` + integer id.

Open questions: none. (Scope-affecting questions - catalog source, apply model, default
fields, v1 phasing - asked and answered by the maintainer 2026-06-17; recorded above.)

## DoR: see worklog for the posted PASS/WATCH/FAIL checklist.
