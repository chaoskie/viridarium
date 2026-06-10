# Proposal - schedule-wrong-reason-404 (bugfix, from 2026-06-10 review pass)

Status: in progress. Bugfix surfaced by the 2026-06-10 quick review pass; tracked as VIRIDARIUM-48.

## Problem

`CareScheduleService.get` and `.delete` skip the plant-exists guard that `upsert` and
`list` perform. A request addressing a **non-existent plant** surfaces as
`CareScheduleNotFoundError` ("No water schedule for plant 999") instead of
`PlantNotFoundForScheduleError` ("Plant 999 not found"): a wrong-reason 404. The module
docstring documents this asymmetry as deliberate, but it misleads automation clients
(the API persona, product-spec section 2) who cannot distinguish "plant has no schedule"
from "plant does not exist" on GET/DELETE, while PUT/LIST on the same resource do make
that distinction.

## Fix (exact scope, PRIN-IX)

Add `self._guard_plant(plant_id)` at the top of `get` and `delete`, consistent with
`upsert`/`list`. Update the module + method docstrings that documented the old behavior.
Status code stays 404 in both cases; only the error reason becomes truthful.

## Out of scope

No router/schema change, no new endpoint, no change to the schedule-missing path for an
existing plant.

## Acceptance

- AC1: `GET /api/v1/plants/{unknown}/schedules/{type}` returns 404 with detail `Plant {id} not found`.
- AC2: `DELETE /api/v1/plants/{unknown}/schedules/{type}` returns 404 with detail `Plant {id} not found`.
- AC3: GET/DELETE for an **existing** plant without that schedule keep the
  `No {type} schedule for plant {id}` detail; all existing tests stay green.

## DoR: PASS (review-surfaced contract-consistency bug; tiny, test-first, no API shape change).
