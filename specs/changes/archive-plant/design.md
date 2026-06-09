# Design - archive-plant (US-2.4)

Modify-only on the merged Plant slice; [TEMPLATE] = inherited Plant pattern.

## Decisions

- **A1 - dedicated idempotent actions.** `POST /api/v1/plants/{id}/archive` and `/unarchive`,
  empty body, return 200 + the updated `PlantResponse`, 404 (reuse `PlantNotFoundError`) for
  unknown id. Idempotent state-set (not toggle): archiving an archived plant -> 200/true, no
  409 - prevents double-click/stale-UI flips. PUT still works as the full-replace path.
- **A2 - list defaults to active.** `PlantFilter` gains `archived: bool | None = None`
  (None/False -> active only; True -> archived only) and `include_archived: bool = False`
  (overrides -> no archived clause = all). Router maps two optional bool query params. Repo:
  `if not include_archived: stmt = stmt.where(PlantModel.archived.is_(bool(archived)))` -
  portable (ARCH-011), AND-composed with the existing clauses, before `order_by(name)`.
- **A3 - no PATCH.** Modeled as POST sub-resource actions, not PATCH (no partial-body merge
  semantics needed). This is the ADR-D escape hatch ("targeted actions introduced when a story
  needs them"); recorded as an ADR-delta note. PATCH stays unused.
- **A4 - reversible -> no confirm dialog.** Archive is one click and undoable (unlike delete,
  which keeps `DeletePlantDialog`); a confirm would fight the one-click goal.

## Backend file plan (modify-only, PRIN-IX)

- `domain/plant.py`: `PlantFilter` += `archived: bool | None = None`, `include_archived: bool
  = False` (+ docstring). `PlantRepository` Protocol += `archive(id)->Plant`, `unarchive(id)->Plant`.
- `application/plants.py`: `PlantService.archive/unarchive` - thin pass-throughs (propagate
  `PlantNotFoundError`; no FK guard - archive doesn't touch location).
- `adapters/outbound/db/plant_repository.py`: the list archived clause (above); `archive`/
  `unarchive` (session-per-call, mirror `update`: `session.get` or raise, flip `model.archived`,
  commit, refresh, `_to_domain` with reloaded tags). Tags untouched -> history retained;
  `updated_at` bumps via existing onupdate.
- `adapters/inbound/web/plants.py`: `list_plants` += `archived: Annotated[bool|None, Query()]
  = None`, `include_archived: Annotated[bool, Query()] = False` -> into `PlantFilter`. Two new
  routes (`POST /{plant_id}/archive`, `/unarchive`) -> `PlantResponse.model_validate(...)`,
  default 200, no request schema.
- **No change:** `schemas.py` (PlantResponse has `archived`; empty action body), `app.py`
  (`PlantNotFoundError`->404 handler exists), `models.py`, `migrations/`, `container.py`,
  `dependencies.py`.

## Frontend file plan (lean, reuse primitives; no new FE-010 primitive)

- `lib/api/plants.ts`: `PlantFilter` += `archived?`, `include_archived?`; `buildQuery` appends
  them when set (mirror `homeless`); `archivePlant(id)`/`unarchivePlant(id)` -> `postJson(.../archive, {})`.
- `features/plants/usePlants.ts`: `archive`/`unarchive` callbacks (call API then reload **with
  the active filter** via a `lastFilterRef` set in `reload`, so a row that crosses the
  active/archived boundary doesn't incoherently vanish/reappear). Add to `UsePlantsResult`.
- `features/plants/PlantsPage.tsx`: a `view` state (`active`|`archived`|`all`) -> a native
  `<select>` in the filter bar (reuse `CONTROL_CLASSES`, not a new primitive) folded into
  `buildFilter`; a per-card ghost `Button` "Archive"/"Unarchive" (label by `plant.archived`),
  `aria-label` set. Archived badge already exists. Default active needs no code (API default).
- `App.tsx`: no change.

## ADR delta

- **Targeted sub-resource actions** (A3): introduced when a story needs non-replace semantics;
  archive/unarchive are the first, as idempotent state-set POSTs returning the resource. PATCH
  remains unused. (Annotates ADR-D from plant-crud/location-crud.)

## Forward link (E3)

Due-computation exclusion (E3) will filter the SAME `archived` flag in the schedule/due query -
no new field. Recorded so E3 doesn't re-invent it.

## Test seed -> test-foundation

Happy+sad per surface; the headline default-excludes-archived; lifecycle (in default -> archive
-> absent -> unarchive -> present, history intact); idempotency; `?archived=true` / `?include_archived=true`;
archived AND other-filter composition; 404 no-PII on both actions; OpenAPI assertion (paths +
the two list params). Unit: service archive/unarchive pass-through + not-found propagation
(extend the fake repo; the list archived clause is repo-SQL -> integration-covered, not unit).
Frontend: `usePlants` archive/unarchive reload-with-retained-filter; client fns. TEST-014 red
per lane. Playwright (deferred): archive via card -> leaves default -> view Archived -> Unarchive -> returns.

## Sizing / delivery

Per-lane: backend ~60-90 prod LOC, frontend ~70-110 - both well under the ~500 soft cap. One
branch, one PR. Parallel disjoint lanes (backend/ vs frontend/); FE builds against §1;
orchestrator cross-checks live OpenAPI + runs the prod-path smoke before merge.
