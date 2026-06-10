# Proposal - potsize-silent-truncation (bugfix, from 2026-06-10 review pass)

Status: in progress. Bugfix surfaced by the 2026-06-10 quick review pass; tracked as VIRIDARIUM-47.

## Problem

A decimal pot size ("3.7") passes the plant form's client-side handling
(`parseOptionalInt` only checks `Number.isFinite`, the number input has no `step`)
and is sent to the API. **Triage correction during reproduction:** the review-pass
claim that Pydantic silently truncates `3.7` to `3` is wrong - Pydantic v2 lax mode
only coerces integral floats, so the server already answers 422. The real defect is
frontend-only: the 422 bounces back as a *wrong-field* error ("The server rejected
this plant. Check the fields." on the name field), with no hint that pot size is the
problem.

## Fix (exact scope, PRIN-IX)

- **Frontend:** integer validation on submit with a field error under pot size
  ("whole number"), the parser tightened to `Number.isInteger`, `step={1}` +
  `aria-invalid` on the input.
- **Backend:** no production change needed. A regression test pins the float-rejects
  behavior (`pot_size_cm: 3.7` -> 422) so a future Pydantic config change cannot make
  it lossy.

## Out of scope

No backend schema change; no UI redesign; no API shape change.

## Acceptance

- AC1: submitting the form with pot size "3.7" shows a pot-size field error, calls no API.
- AC2 (pin): `POST /api/v1/plants` with `pot_size_cm: 3.7` returns 422.
- AC3: integer pot sizes keep working end to end; all existing tests stay green.

## DoR: PASS (review-surfaced UX/validation bug; small, test-first, no contract change).
