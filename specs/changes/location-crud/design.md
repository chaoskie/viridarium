# Design - location-crud (US-2.2)

Approach: the first persisted vertical slice, mirroring the existing `health` slice's style
(`from __future__ import annotations`, frozen `slots=True` domain dataclasses, `Protocol`
ports, `Annotated[..., Depends(...)]` routers, `app.state` wiring). Decisions tagged
**[TEMPLATE]** are the conventions US-2.1 / US-2.4 copy; the cross-cutting ones are recorded
as ADRs (§4) per ARCH-010.

## 1. REST / OpenAPI delta

Resource path `/api/v1/locations` (API-006), tag `locations`, JSON bodies.

**Schemas (adapters/inbound/web/schemas.py):**
- `LocationCreate` (request): `name: str` required, trimmed, `min_length=1`, `max_length=120`
  (whitespace-only -> 422 via `field_validator`); `notes: str | None` optional, `max_length=2000`.
- `LocationUpdate` (request): same fields/validation; **PUT is full-replace** [TEMPLATE].
- `LocationResponse` (response, security boundary ARCH-007, `from_attributes=True`):
  `id: int`, `name: str`, `notes: str | None`, `created_at: datetime`, `updated_at: datetime`.

**Endpoints:**

| Method | Path | Request | Success | Errors |
|---|---|---|---|---|
| POST | `/api/v1/locations` | `LocationCreate` | 201 `LocationResponse` | 422 |
| GET | `/api/v1/locations` | - | 200 `list[LocationResponse]` (order by `name ASC`) | - |
| GET | `/api/v1/locations/{id}` | - | 200 `LocationResponse` | 404 |
| PUT | `/api/v1/locations/{id}` | `LocationUpdate` | 200 `LocationResponse` | 404, 422 |
| DELETE | `/api/v1/locations/{id}` | - | 204 (no body) | 404 |

No 409 this story (no uniqueness, no non-empty guard - both deferred). Only 404 + 422 sad paths.

## 2. Backend file plan

**domain/location.py** (new, framework-free): `Location` dataclass (id, name, notes,
created_at, updated_at); `NewLocation` dataclass (name, notes - no server-set fields);
`LocationNotFoundError(location_id)` (no PII); `LocationRepository` Protocol with
`add(NewLocation)->Location`, `list_all()->list[Location]`, `get(id)->Location`,
`update(id, name, notes)->Location`, `delete(id)->None` (get/update/delete raise on missing).
**[TEMPLATE]:** persisted `Entity` + `NewEntity` pair, typed `XNotFoundError`, port raises
domain errors and never returns framework types.

**application/locations.py** (new, depends only on domain): `LocationService(repository)` with
thin `create/list/get/update/delete` wrapping the port; returns domain types (ARCH-007).
**[TEMPLATE]:** one `XService` per aggregate, constructor-injected with its port; logic lands
here when entities gain real rules (due computation, archive exclusion).

**adapters/inbound/web/locations.py** (new): `APIRouter(prefix="/locations", tags=["locations"])`
with the five routes; no business logic; maps `Location` -> `LocationResponse`
(`model_validate(loc, from_attributes=True)`); 404 handled by the registered exception handler
(not per-route try/except). DELETE returns `Response(status_code=204)`.

**adapters/inbound/web/schemas.py** (modify): add the three schemas alongside `HealthResponse`
(same public surface, ARCH-008). Split into a `schemas/` package only if it passes ~250 LOC (QG-009).

**adapters/inbound/web/dependencies.py** (modify): add
`get_location_service(request) -> LocationService` reading `request.app.state.location_service`.

**adapters/outbound/db/models.py** (new): `LocationModel(Base)`, `__tablename__="location"`:
`id` PK Integer; `name` String(120) NOT NULL; `notes` String(2000) NULL; `created_at`
DateTime(timezone=True) NOT NULL server_default `func.now()`; `updated_at` same +
`onupdate=func.now()`. Portable types only (ARCH-011). **[TEMPLATE]:** all ORM models live here.

**adapters/outbound/db/location_repository.py** (new): `SqlAlchemyLocationRepository(session_factory)`;
session-per-call; commits writes; module-level `_to_domain(model)->Location` is the sole
ORM<->domain mapping site (anti-corruption, ARCH-009); raises `LocationNotFoundError` on missing
rows; `list_all` orders by `name`. **[TEMPLATE]:** session-per-call, repo owns its commits + mapping.

**adapters/outbound/db/migrations/versions/0002_create_location.py** (new): revision `0002`,
`down_revision="0001"`; `op.create_table("location", ...)` with the columns above and
`sa.PrimaryKeyConstraint("id", name="pk_location")` (naming-convention aligned for SQLite
batch stability); `downgrade` drops the table. Server-default timestamps in DDL; `onupdate`
is app-side ORM behavior, not a DB constraint.

**infrastructure/container.py** (modify): build `SqlAlchemyLocationRepository(session_factory)`
+ `LocationService(repo)`; add `location_service: LocationService` to the `Container` dataclass.

**infrastructure/app.py** (modify): include the locations router in `_build_api_router`; set
`app.state.location_service = container.location_service`; register
`@app.exception_handler(LocationNotFoundError)` -> `JSONResponse(404, {"detail": str(exc)})`.
**[TEMPLATE]:** error-to-HTTP via one registered handler per domain error class; no HTTP codes
in application/domain; bodies carry no PII.

## 3. Frontend file plan

Plain `fetch` + React hooks, **no react-query / no new deps** (avoids a stack amendment).
FE-008: no cross-feature imports; shared primitives in `components/ui/`. Page is "Rooms" (D-008).

**lib/api/client.ts** (modify): add `postJson<T>(path, body)`, `putJson<T>(path, body)`,
`deleteResource(path)` (204 -> void), reusing the existing `ApiError` pattern.

**lib/api/locations.ts** (new): `Location` + `LocationInput` interfaces; typed
`fetchLocations/fetchLocation/createLocation/updateLocation/deleteLocation`. **[TEMPLATE]** for `plants.ts`.

**components/ui/Button.tsx, TextField.tsx, Modal.tsx** (new): minimal token-styled primitives
(FE-001). Button variants primary/ghost/danger, `min-h-tap-min` taps (FE-011). TextField =
labeled input/textarea with `error?` slot + `multiline?`. Modal = accessible dialog
(`role="dialog"`, `aria-modal`, Escape-to-close, backdrop). No generic Form / toast (YAGNI).

**features/rooms/useLocations.ts** (new): hook owning `locations/loading/error` + `reload/create/update/remove`;
`useEffect` loads on mount; mutations call API then `reload()`; `ApiError` -> human message.
**[TEMPLATE]:** one `useXs` hook per feature.

**features/rooms/RoomsPage.tsx** (new): list view (h1 "Rooms", "Add room" button, loading/empty/error
states, per-room Edit + Delete). **RoomFormModal.tsx** (new): create/edit form in a Modal,
client-side required-name mirror + server-422 surfacing. **DeleteRoomDialog.tsx** (new): plain
confirm delete; code comment notes the US-2.1 plant-aware flow.

**App.tsx** (modify): `/rooms` -> `<RoomsPage />` (leave other placeholders untouched, PRIN-IX).

## 4. ADR decisions (cross-cutting, ARCH-010) - recorded here as the change's design ADRs

- **ADR-A Timestamps on every entity.** Server-set `created_at`/`updated_at`
  (`DateTime(timezone=True)`, `server_default=func.now()`, ORM `onupdate`), absent from request
  schemas (not client-controllable). Rationale: cheap, engine-portable, needed by history/export/
  ordering (US-3.4, US-5.6); infrastructural metadata, not new domain behavior (SPEC-001-safe). Template.
- **ADR-B Repository-port shape is the aggregate template.** `XRepository` Protocol +
  `X`/`NewX` dataclasses + `XNotFoundError`; concrete `SqlAlchemyXRepository` owns session-per-call
  + sole ORM<->domain mapping. Plant/CareSchedule/CareEvent inherit this.
- **ADR-C Error-to-HTTP via registered handlers.** Domain raises typed errors; app factory maps
  each to a status (`{"detail": ...}`, no PII). 404 now; 409 reserved for future guards.
- **ADR-D PUT full-replace, no PATCH** until a story needs partial semantics (API-005 stable shape).
- **ADR-E No unique constraint on `name`** (duplicate room names are legal per spec).

(Recorded inline as design ADRs rather than separate `decisions/` notes; the product-level
homeless/delete-flow decision is the standalone D-009. Promote any of A-C to a numbered ADR if
US-2.1 needs to cite it independently.)

## 5. Context-pollution watch (ARCH-004 standing duty)

Location/Plant/CareSchedule/CareEvent form one inventory+care bounded context - correct as a
single hexagon now. Watch signal: SpeciesInfo (US-6) or webhooks (US-5.4) pulling Location/Plant
entities into unrelated orchestration -> propose carving a context. Not actionable this story.

## 6. Delivery (PRIN-VI parallel disjoint-file)

Two build agents under the orchestrator: **backend** owns everything under `backend/`;
**frontend** owns everything under `frontend/`. No shared files (the Makefile already has
separated sections and needs no edit). Frontend builds against the §1 contract; the orchestrator
re-runs gates and verifies the live OpenAPI matches the typed client before commit. One branch,
one PR (one user story).
