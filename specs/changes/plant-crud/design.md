# Design - plant-crud (US-2.1)

Mirrors the US-2.2 Location vertical slice; [TEMPLATE] = the inherited Location pattern,
not re-justified. Novel decisions justified against ARCH-011 / D-009.

## Key decisions

- **D1 - Plant.location FK on delete = nullable FK + `ON DELETE SET NULL`.** Deleting a room
  auto-orphans its plants to homeless (D-009 option C baseline; no FK violation, no data loss,
  no plant deletion). The rich A/B/C prompt stays deferred. **Critical:** SQLite ignores FK
  actions unless `PRAGMA foreign_keys=ON` is set per connection - it is NOT today. Fix: a
  `connect` event listener in `engine.py` issuing the pragma for SQLite only (engine-isolated,
  harmless to Postgres). Without it, SET NULL silently no-ops on SQLite while Postgres enforces
  it - a cross-engine divergence. Migration declares the FK as
  `ForeignKeyConstraint([...], ondelete="SET NULL", name="fk_plant_location_id_location")`
  (naming-convention aligned for SQLite batch stability). MUST have a dual-engine test.
- **D2 - tags = normalized `plant_tag(plant_id, tag)` child table**, NOT a JSON column.
  Filterability (`?tag=`) must be portable; JSON filtering is engine-specific SQL (ARCH-011
  forbids on the critical path). Child table filters via portable `EXISTS`. `plant_tag` FK to
  plant `ON DELETE CASCADE`; composite PK `(plant_id, tag)`; domain holds `tags: tuple[str,...]`.
- **D3 - enums = `StrEnum` in domain, stored as `String(20)`.** No native DB enum types
  (non-portable, ARCH-011). Values use the spec wire form (`bright-indirect`, `full-sun`,
  `self-watering`). Pydantic validates → 422 on bad value.
- **D4 - search/filter:** query params `q` (lowered-LIKE over name|species), `location_id`
  (exact), `tag` (EXISTS on plant_tag), `species` (lowered-LIKE), `homeless` (location_id IS
  NULL). All optional, AND-combined, none → all ordered by `name ASC`. Portable: lowercase both
  sides of LIKE (SQLite case-folds ASCII, Postgres doesn't); EXISTS for tags. Unknown
  `location_id` as a *filter* → empty list (not an error).
- **D5 - timestamps per ADR-A; `archived` persisted + exposed but inert** (no exclusion logic
  here - that's US-2.4). List does not filter archived out.

## 1. REST / OpenAPI delta

Path `/api/v1/plants` (API-006), tag `plants`.

**`PlantCreate`** (request): `name` (req, trimmed, 1-120, reuse `_trim_non_empty_name`),
`species` (opt, ≤200), `location_id` (opt int, null=homeless), `acquired_on` (opt date),
`pot_size_cm` (opt int, 1-500), `pot_material` (opt `PotMaterial`), `light_level` (opt
`LightLevel`), `notes` (opt, ≤10000), `tags` (list[str], default [], each trimmed non-empty
≤50, deduped, ≤50 items), `archived` (bool, default false).
**`PlantUpdate(PlantCreate)`** - full-replace (ADR-D).
**`PlantResponse`** (`from_attributes=True`): id, name, species, location_id, acquired_on,
pot_size_cm, pot_material, light_level, notes, tags (list), archived, created_at, updated_at.
**List query:** `q`, `location_id`, `tag`, `species`, `homeless` (all optional).

| Method | Path | Req | Success | Errors |
|---|---|---|---|---|
| POST | `/api/v1/plants` | PlantCreate | 201 PlantResponse | 422 (body/enum/date); **422 unknown location_id** |
| GET | `/api/v1/plants` | query params | 200 list (name ASC) | 422 (bad param type) |
| GET | `/api/v1/plants/{id}` | - | 200 | 404 |
| PUT | `/api/v1/plants/{id}` | PlantUpdate | 200 | 404 (plant), 422 (body / unknown location_id) |
| DELETE | `/api/v1/plants/{id}` | - | 204 | 404 |

Unknown `location_id` on create/update → **422** via `LocationNotFoundForPlantError` (it's a
body-reference validation failure; 404 is reserved for the addressed plant). No 409.

## 2. File plan

**Backend - new:** `domain/plant.py` (`PotMaterial`/`LightLevel` StrEnums; `Plant`/`NewPlant`/
`PlantFilter` frozen dataclasses; `PlantNotFoundError`, `LocationNotFoundForPlantError`;
`PlantRepository` Protocol: `add/list(filter)/get/update(id,new)/delete/location_exists`);
`application/plants.py` (`PlantService` - the FK-existence guard on create/update is the real
logic, ADR-B); `adapters/outbound/db/plant_repository.py` (`SqlAlchemyPlantRepository`, sole
`_to_domain` mapping, portable filter query building, tag write/replace);
`migrations/versions/0003_create_plant.py` (`plant` + `plant_tag`, FK ondelete, down_rev 0002);
`adapters/inbound/web/plants.py` (5 routes + list query→`PlantFilter`).

**Backend - modify (minimal, PRIN-IX):** `models.py` (+`PlantModel` w/ `location_id`
ForeignKey ondelete SET NULL, +`PlantTagModel`; `LocationModel` untouched); **`engine.py`**
(the SQLite `PRAGMA foreign_keys=ON` connect listener - D1); `schemas.py` (+3 Plant schemas,
reuse `_trim_non_empty_name`); `dependencies.py` (+`get_plant_service`); `container.py`
(+repo+service+field); `app.py` (+router, +`app.state.plant_service`, +`PlantNotFoundError`→404
and `LocationNotFoundForPlantError`→422 handlers).

**Frontend - new:** `lib/api/plants.ts` (types incl. enum unions + `PlantFilter`; 5 fns;
`fetchPlants` builds the query string); `features/plants/usePlants.ts` (hook, reload takes the
filter); `PlantsPage.tsx` (list + filter controls bar + reuses `fetchLocations` for the room
dropdown/names - `lib/api` is shared infra, FE-008 only forbids cross-*feature* imports);
`PlantFormModal.tsx` (all fields; location picker with a "No room (homeless)" option → null;
enum `<select>`s; tags input); `DeletePlantDialog.tsx` (plain confirm, [TEMPLATE]).
**Frontend - modify:** `App.tsx` (`/plants` → `<PlantsPage />`; others untouched).
**Select:** native `<select>` styled with existing tokens inline (FE-010 - not a 3rd primitive;
raise an ADR only if duplicated 3+ times). Modal focus-trap hardening only if cheap (else stays
filed).

## 3. ADR delta

Inherits ADRs A-E from location-crud unchanged. New conventions:
- **Cross-aggregate existence check** lives in the application service (`location_exists` on the
  port), mapped to **422** (body-reference failure), distinct from the 404 not-found of the
  addressed aggregate. Reusable when future entities reference others.
- **FK on-delete = SET NULL for optional references** (orphan, don't cascade-delete) where the
  referenced entity's loss shouldn't destroy the referrer; **CASCADE** for owned children
  (`plant_tag`). Both require the SQLite pragma.
- These are recorded here + a consequences note on **D-009** (SET NULL = option C baseline);
  no separate ADR needed (D-009 already ratifies the behavior).

## 4. Test seed → test-foundation (test-engineer authors)

Input-state matrix (TEST-007) over name/species/location_id/acquired_on/pot_size_cm/
pot_material/light_level/tags/notes/archived; branch-priority name→enum→fk→bounds→optional.
Happy+sad per surface; search/filter cases (each param + AND combination); **the ON DELETE
SET NULL cross-entity test on BOTH engines** (room delete → plant homeless, survives) - which
fails on SQLite without the pragma (useful TEST-014 red); `plant_tag` CASCADE test. Unit:
`PlantService` FK-guard against a fake port. Integration: full CRUD + filter through real DB.
Migration `0003` up/down. OpenAPI assertion. **TEST-014 red-run evidence mandatory per lane.**

## 5. Sizing (per-lane, SPEC-004 amendment)

Backend ~430-480 (search/filter + tags are the bulk) - under the ~500 per-lane soft cap, do
NOT split. Frontend ~430-500 (PlantFormModal heaviest) - attempt as one lane; **pre-agreed
fallback** if it crosses ~500: defer the filter *controls* (not the API) to a thin follow-up.
1000 hard ceiling per story respected.

## 6. Delivery (PRIN-VI parallel lanes)

Backend owns `backend/`, frontend owns `frontend/`, zero shared files. Frontend builds against
§1; orchestrator re-runs gates, cross-checks live OpenAPI vs the typed client, and runs the
prod-path smoke test (backend-served build, zero console errors) before commit. One branch
(`feat/us-2.1-plant-crud`), one PR.
