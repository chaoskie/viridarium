# Test-foundation - plant-cachepot (US-2.x)

Status: G0, authored before implementation (SPEC-003). Author: test-engineer.

This foundation governs the descriptive-only outer-pot (cachepot) addition: a dedicated
`OuterPotMaterial` StrEnum and two nullable fields `outer_pot_material` +
`outer_pot_size_cm` on the plant, additive and non-breaking. The existing
`pot_material` / `pot_size_cm` stay as the inner/nursery pot (D1, not renamed).

It is binding at the story-complete re-audit (TEST-015): every planned test below maps
to a named implemented test or a worklogged deferral, or the DoD gate blocks.

---

## 0. Strategy + shape (TEST-001 HoneyComb)

- **Integration is primary.** The outer-pot fields are validated by Pydantic and
  persisted through the real router -> service -> repository -> SQLAlchemy -> SQLite
  slice. The behaviour bar (accept valid, reject invalid -> 422, round-trip, null
  defaults) is met by extending `backend/tests/integration/test_plants_endpoint.py`
  and `backend/tests/integration/test_migrations.py`. Nothing internal is mocked
  (TEST-003).
- **Unit only where it earns its place.** A small unit test for the new enum
  (`OuterPotMaterial` members + wire values) and the entity carrying/threading the two
  new fields is the only new unit-layer work: pure domain, no I/O (TEST-002). No unit
  test duplicates a cell the integration slice already covers (TEST-004 redundancy bar).
- **Acceptance stays thin (TEST-009).** One Playwright journey: add a plant with an
  outer pot, persist, read it back; plus re-running the existing S25+ reachability and
  axe a11y checks now that the modal has the extra fields. No new full journeys beyond
  the one the data unlocks.
- **Frontend unit (vitest):** API-client round-trip of the two new fields and the form
  set/clear/submit-null behaviour + inner-pot relabel.

This is descriptive-data-only work (design D5): there is NO due/schedule/waterlogging
logic to test in this change. Tests asserting care behaviour would be out-of-scope noise.

---

## 1. Outer-pot input-state matrix (TEST-007)

The create/update body gains two independent optional dimensions; combined with the
"both fields independently optional" requirement this is >=3 dimensions / >=6 cells, so
an explicit matrix with named branch-priority order is required.

### 1a. Dimensions

| Dim | Field | Values under test |
|-----|-------|-------------------|
| D-MAT | `outer_pot_material` | each valid enum value (7) / invalid string / null / omitted |
| D-SIZE | `outer_pot_size_cm` | null / omitted / 1 (min) / 500 (max) / 0 (below) / 501 (above) / "big" (non-int) / 3.7 (float) |
| D-INDEP | pairing | material set + size null; material null + size set; both set; both null |

### 1b. Branch-priority order (highest first)

1. **B1 valid material accepted + echoed** - each of the 7 enum values round-trips (the headline AC1 happy path). Critical path.
2. **B2 invalid material -> 422** - unknown enum string rejected (AC1 sad). Critical path.
3. **B3 size boundary accepted** - 1 and 500 accepted + echoed (AC1 happy, boundary).
4. **B4 size out-of-range -> 422** - 0 and 501 rejected (AC1 sad, boundary).
5. **B5 size type-strict -> 422** - "big" (non-int) and 3.7 (float, never silently truncated) rejected. Mirrors the VIRIDARIUM-47 float guard already proven for `pot_size_cm`.
6. **B6 independent optionality** - material-only (size null), size-only (material null), both null all accepted; both echo correctly.
7. **B7 null/omitted default** - omitting either field reads back null (overlaps §2).

### 1c. Expected-result cells

Valid-material cells (B1), parametrized over `list(OuterPotMaterial)`:

| `outer_pot_material` | Expected |
|----------------------|----------|
| ceramic | 201, echoes "ceramic" |
| terracotta | 201, echoes "terracotta" |
| plastic | 201, echoes "plastic" |
| metal | 201, echoes "metal" |
| woven | 201, echoes "woven" |
| glass | 201, echoes "glass" |
| other | 201, echoes "other" |

Size cells (B3-B5):

| `outer_pot_size_cm` | Expected | Branch |
|---------------------|----------|--------|
| null / omitted | 201, echoes null | B7 |
| 1 | 201, echoes 1 | B3 |
| 500 | 201, echoes 500 | B3 |
| 0 | 422 | B4 |
| 501 | 422 | B4 |
| "big" (string) | 422 | B5 |
| 3.7 (float) | 422 (never truncated) | B5 |

Material sad cell (B2):

| `outer_pot_material` | Expected |
|----------------------|----------|
| "wicker" / "gold" (not in enum) | 422 |
| "self-watering" (an inner-only value, deliberately NOT in OuterPotMaterial per D2) | 422 |

Independent-optionality cells (B6):

| material | size | Expected |
|----------|------|----------|
| "ceramic" | null | 201, material="ceramic", size=null |
| null | 30 | 201, material=null, size=30 |
| "woven" | 22 | 201, both echoed |
| null | null | 201, both null (a bare nursery-pot plant) |

### 1d. New entries appended to the shared `_BAD_BODIES` matrix

The existing parametrized matrix (run for both POST and PUT) gains:

- `outer-pot-material-invalid`: `{"name":"ok","outer_pot_material":"wicker"}`
- `outer-pot-material-self-watering-rejected`: `{"name":"ok","outer_pot_material":"self-watering"}` (D2: deliberately not a valid outer value)
- `outer-pot-size-below-min`: `{"name":"ok","outer_pot_size_cm":0}`
- `outer-pot-size-above-max`: `{"name":"ok","outer_pot_size_cm":501}`
- `outer-pot-size-non-int`: `{"name":"ok","outer_pot_size_cm":"big"}`
- `outer-pot-size-float-not-coerced`: `{"name":"ok","outer_pot_size_cm":3.7}`

These flow through both `test_post_validation_rejects_bad_body` and
`test_put_validation_rejects_bad_body` automatically (one matrix, two parametrized
runners) - so each new cell is asserted as a 422 on BOTH POST and PUT (TEST-005 sad
per surface, both write surfaces).

---

## 2. Null-default + non-regression cases

- **Bare-nursery-pot plant reads back null/null.** A plant created with no outer-pot
  fields (or with both omitted) responds with `outer_pot_material: null` and
  `outer_pot_size_cm: null`, and re-fetches identically (the existing
  full-round-trip equality assertion pattern).
- **Existing single-pot plants unaffected (AC2).** The existing
  `test_post_creates_homeless_plant` / `test_post_creates_plant_full_and_round_trips`
  stay green; the two new fields default to null without any client change. The minimal
  `{"name":"Pothos"}` body still 201s and now also reports the two null fields.
- **Inner pot is untouched.** Setting outer-pot fields does not alter
  `pot_material` / `pot_size_cm`; a body carrying both inner and outer pots round-trips
  all four fields independently (one explicit integration test).

---

## 3. Migration 0008 - dual-engine up/down (ARCH-011, AC3)

`migrations/versions/0008_add_cachepot_columns.py` (down_revision = `0007`) adds two
nullable columns (`outer_pot_material` `String(20)`, `outer_pot_size_cm` `Integer`) to
the `plant` table in batch mode; downgrade drops both.

Extend `backend/tests/integration/test_migrations.py` (the existing column-set
assertions are the precedent):

- **M1 SQLite up adds columns.** `test_upgrade_adds_cachepot_columns_and_downgrade_drops_them`
  (sqlite): after `upgrade head`, the `plant` column set equals the prior set PLUS
  `{outer_pot_material, outer_pot_size_cm}`; both columns are nullable.
- **M2 SQLite down drops columns.** After `downgrade "0007"`, the `plant` column set is
  exactly the pre-0008 set again (the two columns are gone, the table and all 0003
  columns survive). Reversibility proven, batch-mode-safe.
- **M3 existing rows get NULL on up.** Seed a `plant` row at `0007` (before 0008), run
  `upgrade head`, assert the existing row now reads `outer_pot_material IS NULL` and
  `outer_pot_size_cm IS NULL` - no backfill, no default (D3). This is the trippable-data
  half (QG-015): the row must exist for the NULL-on-existing-row property to be reachable.
- **M4 PostgreSQL up/down (ARCH-011 cross-engine).** The same up-then-down assertions
  run against the PostgreSQL service. Mark with the existing cross-engine mechanism the
  migration suite already uses for Postgres (the CI Postgres path per cicd.md); if the
  current suite covers Postgres only in CI, M4 is the CI-gated mirror of M1/M2 and is
  recorded as such in the worklog rather than duplicated as a locally-skipped test.

Down_revision correctness is implicitly asserted by `upgrade head` reaching 0008 and the
column appearing; an explicit head-linearity check is not added (no precedent, would be
redundant with the existing chain tests).

---

## 4. Contract / OpenAPI codegen-output assertion (TEST-008, AC5)

Extend `test_openapi_exposes_plant_paths_query_params_and_schema` (the existing
`PlantResponse` property-set assertion is the precedent and the single source of truth
for "additive, non-breaking"):

- **C1 PlantResponse gains both properties.** The `PlantResponse` `properties` key-set
  equals the current set PLUS `{outer_pot_material, outer_pot_size_cm}` (extend the
  existing exact-set assertion - this is what makes a *removed* or *renamed* field fail,
  proving additive-only).
- **C2 PlantCreate + PlantUpdate gain both properties.** Assert both new properties are
  present on the `PlantCreate` and `PlantUpdate` request schemas.
- **C3 size bounds in the schema.** Assert the emitted `outer_pot_size_cm` schema carries
  `minimum: 1` / `maximum: 500` (the contract bound, not just the runtime 422) and is
  nullable (anyOf integer/null or `nullable`), matching the existing `pot_size_cm` shape.
- **C4 material enum in the schema.** Assert the emitted `outer_pot_material` enum lists
  exactly the 7 `OuterPotMaterial` wire values and is nullable.
- **C5 inner-pot contract unchanged.** `pot_material` / `pot_size_cm` remain present with
  the same names and bounds (the rename-would-break guard, D1). Covered by C1's exact
  key-set assertion retaining `pot_material`/`pot_size_cm`.

The live OpenAPI-vs-typed-client cross-check (G7) confirms the frontend union types
match the emitted enum - any drift (e.g. a value added server-side but not in
`OUTER_POT_MATERIALS`) surfaces there.

---

## 5. Frontend (vitest)

### 5a. API client (`plants.test.ts`)

- **F1 round-trips the new fields.** Extend `SAMPLE` + `INPUT` with
  `outer_pot_material` + `outer_pot_size_cm`; the create/fetch round-trip equality
  assertions now cover them (the body is `JSON.stringify(INPUT)`, so a missing field
  fails the existing `toHaveBeenCalledWith` body assertion).
- **F2 null outer pot serialized.** `HOMELESS_INPUT` (or a new bare-input fixture)
  carries `outer_pot_material: null` + `outer_pot_size_cm: null` and the POST body
  asserts both nulls cross the wire (mirrors the existing homeless-null pattern).
- **F3 OUTER_POT_MATERIALS completeness.** Assert `OUTER_POT_MATERIALS` equals the 7
  expected wire values in order (the select-source-of-truth guard; mirrors the implicit
  `POT_MATERIALS` usage). This is the frontend half of C4.

### 5b. Form (`PlantFormModal.test.tsx`)

- **F4 sets outer material + size and submits them.** Fill name, select an outer
  material, type an outer size; submit; assert `onSubmit` called with
  `{outer_pot_material: "<value>", outer_pot_size_cm: <int>}`.
- **F5 submits null when unset.** Fill only the name; submit; assert the input carries
  `outer_pot_material: null` and `outer_pot_size_cm: null` (the "Not set" default and
  blank size -> null via `parseOptionalInt`, mirroring the existing inner-pot behaviour).
- **F6 clears a previously-set outer pot.** Render in edit mode with an outer pot set;
  change material back to "Not set" and clear the size; submit; assert both null
  (the AC4 "can clear" half).
- **F7 outer size rejects a decimal (field guard).** Mirror the VIRIDARIUM-47 inner-pot
  decimal test for the outer size input if the form applies the same whole-number guard;
  if the form relies solely on `parseOptionalInt` (silent null) rather than a field
  error, F7 instead asserts the submitted value is null for "3.7" and the server 422
  (B5) is the backstop. The build agent records which guard the form uses; one of the
  two assertions must be present (TEST-005 sad path for the outer size control).
- **F8 inner-pot relabel present (AC4).** Assert a "Nursery (inner) pot" label/heading
  is rendered and the existing inner controls sit under it; assert an
  "Outer / decorative pot" section label is present. This is the relabel regression guard.

---

## 6. Acceptance (Playwright, TEST-009, AC2 + AC4)

Add to `frontend/e2e/` (extend `add-plant-modal.spec.ts` or a sibling spec; extend the
`PlantFormComponent` `.co.ts` with the two new outer-pot locators):

- **A1 add-plant-with-outer-pot persists and reads back.** Open the modal, fill name,
  select an outer material, fill an outer size, submit; the plant appears on the list;
  open/detail (or re-open) shows the outer pot persisted. Drives real UI affordances
  only (no value injection). This is the end-to-end proof of AC2 + AC4 through the
  running backend.
- **A2 modal reachability holds with the extra fields (S25+).** The existing BUG-003
  reachability check still passes - the Name field is reachable and the new fields do
  not push it out of a scrollable modal on the galaxy-s25-plus viewport.
- **A3 axe a11y with the extra fields.** Call `expectNoSeriousA11yViolations(page)`
  with the modal open and the new controls present (FE-015) - every new control is
  labelled (FE-011); no new serious/critical violation.
- **A4 console-error clean (TEST-010).** Inherited via the `failOnConsoleError`
  auto-fixture; no allowlist entry is added.

FE-012 design-review screenshots (phone + desktop) of the updated form are captured by
the orchestrator at G7 (`screenshots.spec.ts` already shoots the add-plant modal at both
breakpoints; the new fields appear automatically).

---

## 7. Coverage targets + markers (QG-002, TEST-012)

- **Overall floor 85%; diff-cover >=80% on the new code** (the two schema fields, the
  enum, the model columns + `_to_domain` mapping, the migration, the frontend additions).
- **Branch coverage:** domain/application >=95%, adapters/outbound >=80%. The new enum and
  the `_to_domain` material-string -> `OuterPotMaterial | None` mapping (the only new
  branch in outbound) must be exercised by the round-trip + null-default integration
  tests; the both-null and material-set-size-null cells force the None branch.
- **No flagged critical-100% path** in this change (descriptive data, no care logic,
  SEC: no new sensitive data per proposal). If the reviewer flags the migration
  reversibility as critical, M1+M2 already give it 100% up/down coverage; a sanctioned
  mutation probe (drop one `op.add_column` / break the down-drop) at story-complete
  proves M1/M3/M2 fail on regression - logged in the audit report if run.
- **Markers (TEST-012):** every new/extended Python test file keeps its module-level
  `pytestmark = pytest.mark.integration` (endpoint + migration) or
  `pytestmark = pytest.mark.unit` (the new enum/entity unit file). Frontend tests run
  under vitest; e2e under Playwright projects (galaxy-s25-plus untagged, @desktop tagged).

---

## 8. TEST-014 red-before-green expectation (per lane)

Two disjoint lanes; each records its own red in the change worklog before the green
commit:

- **Backend lane (G1-G4):** before adding the enum/fields/columns/migration, the
  extended `test_plants_endpoint.py` cells (B1-B7), the `_BAD_BODIES` additions, the
  migration M1-M3, and the OpenAPI C1-C5 assertions FAIL (unknown enum value, missing
  schema properties, missing columns). Record the failing test names + the assertion/error
  output (e.g. `KeyError: 'outer_pot_material'` on the OpenAPI property set; `422` not
  returned for a now-valid material; missing-column on the migration inspect) before the
  implementation commit.
- **Frontend lane (G5-G6):** before adding the client fields / form section, F1-F8 FAIL
  (type error / missing label / `onSubmit` body mismatch). Record the red.

The characterisation-test carve-out used previously (PlantFormModal partial-fill suite)
does NOT apply here: F4-F8 assert NEW behaviour and must be genuinely red-first. F8's
relabel assertion is red until the heading lands. Any deviation is comply-or-explain in
the worklog.

---

## 9. Scenario -> test traceability (TEST-015)

Each proposal AC maps to named planned tests. Filled with the final implemented test
names at the story-complete re-audit; a scenario with neither a named test nor a
worklogged deferral blocks the DoD gate.

| AC | Scenario | Planned test(s) | Layer |
|----|----------|-----------------|-------|
| AC1 | POST/PUT accept valid outer material (each enum) + size 1-500; invalid enum / out-of-range -> 422 | `test_post_each_outer_pot_material_round_trips` (param over `OuterPotMaterial`, B1); `test_post_outer_pot_size_boundaries_round_trip` (1/500, B3); `_BAD_BODIES` cells `outer-pot-material-invalid`, `outer-pot-material-self-watering-rejected`, `outer-pot-size-below-min`, `outer-pot-size-above-max`, `outer-pot-size-non-int`, `outer-pot-size-float-not-coerced` via `test_post_validation_rejects_bad_body` + `test_put_validation_rejects_bad_body` (B2/B4/B5); `test_outer_pot_fields_independently_optional` (B6) | integration (+ unit for enum members) |
| AC2 | Response returns both fields; plant created without them reads back null/null; existing single-pot plants unaffected | `test_post_outer_pot_null_when_unset_round_trips` (§2); existing `test_post_creates_homeless_plant` + `test_post_creates_plant_full_and_round_trips` stay green; e2e `add-plant with an outer pot persists + reads back` (A1) | integration + e2e |
| AC3 | Migration 0008 applies + reverses cleanly on SQLite AND PostgreSQL; existing rows get NULL | `test_upgrade_adds_cachepot_columns_and_downgrade_drops_them` (M1/M2, sqlite); `test_existing_plant_row_gets_null_cachepot_columns_on_upgrade` (M3); Postgres cross-engine mirror (M4, CI-gated) | integration |
| AC4 | Add/edit form sets + clears outer material + size; inner-pot fields relabelled "Nursery (inner) pot" | `PlantFormModal` F4 (sets+submits), F5 (null when unset), F6 (clears), F8 (relabel present); e2e A1 (drives the real form) | frontend unit + e2e |
| AC5 | Existing plant tests stay green; no contract break (existing clients keep working) | OpenAPI C1-C5 (additive-only, inner-pot names unchanged); full existing `test_plants_endpoint.py` + `plants.test.ts` suites stay green; live OpenAPI-vs-typed-client cross-check (G7) | integration + frontend + acceptance gate |

---

## 10. Planned-test count by layer (summary)

- **Backend unit:** 2 (OuterPotMaterial enum members/wire-values; entity carries+threads the two fields).
- **Backend integration - endpoint:** ~6 new named tests + 6 new `_BAD_BODIES` cells (each cell x POST and PUT = 12 parametrized sad assertions): valid-material param (7 cases), size-boundary, independent-optionality (4 cells), null-default, inner+outer-coexist, OpenAPI C1-C5 (extends 1 existing test).
- **Backend integration - migration:** 3 named (M1/M2 combined up-down, M3 null-on-existing-row) + M4 Postgres CI mirror.
- **Frontend unit:** ~3 client (F1-F3) + ~5 form (F4-F8).
- **Acceptance (Playwright):** 1 new journey (A1) + reuse of A2 reachability / A3 axe / A4 console-error.

HoneyComb check: integration is the bulk (endpoint + migration), units are 2 targeted +
the frontend form/client, acceptance is a single thin journey - shape compliant (TEST-001).
