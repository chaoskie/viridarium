---
title: Test Foundation - photos (US-2.3)
type: test-foundation
change: photos
status: authored
date: 2026-06-09
---

# Test Foundation - photos (US-2.3)

Pre-implementation test foundation for the `Photo` aggregate (SPEC-003 artifact gating).
This is the most security-sensitive E2 story: the upload-validation, no-PII-leak, and
path-traversal-safe-naming paths are **first-class, critical-100%** lanes here, not
afterthoughts. Authored by `test-engineer/HIGH` against `design.md` (P1-P6, the REST
delta, the file plan) and `proposal.md` (scope/AC1-AC11, the Security section).

This document is **prescriptive** (input matrices, named cases, layer + coverage
assignment, mocking boundary). It contains **no test code**. The build agents (backend
lane, frontend lane) implement against it and record the TEST-014 red per lane before
turning it green. The story-complete pass re-audits the implementation against this
foundation and issues the approval (DoD §3).

---

## 1. Surface inventory (what gets a happy + a sad, TEST-005)

Every public surface below carries **≥1 happy and ≥1 sad** test. The five endpoints and
the use-case methods are the security-bearing surfaces; the sniff is the pure security
primitive.

| # | Surface | Kind | Happy | Sad (≥1) |
|---|---|---|---|---|
| E1 | `POST /plants/{id}/photos` (upload) | endpoint | 201 + metadata | 413 / 415 ×3 / 404-plant / 422-no-file |
| E2 | `GET /plants/{id}/photos` (list) | endpoint | 200 newest-first | 404-plant |
| E3 | `GET /plants/{id}/photos/{photo_id}` (bytes) | endpoint | 200 bytes + ct + cache | 404 photo / cross-plant 404 |
| E4 | `POST /plants/{id}/photos/{photo_id}/cover` | endpoint | 200 flips one | 404 photo / cross-plant 404 |
| E5 | `DELETE /plants/{id}/photos/{photo_id}` | endpoint | 204 | 404 photo / cross-plant 404 |
| S1 | `PhotoService.upload` | use case | happy persist+cover | oversize / bad-magic / mismatch / missing-plant |
| S2 | `PhotoService.list` | use case | newest-first | (covered via repo + endpoint) |
| S3 | `PhotoService.get` | use case | returns row | `PhotoNotFoundError` (incl. cross-plant) |
| S4 | `PhotoService.set_cover` | use case | single cover in-tx | `PhotoNotFoundError` |
| S5 | `PhotoService.delete` | use case | row+file gone; promotes survivor | `PhotoNotFoundError`; storage.delete after repo.delete |
| Z1 | `sniff_image_type(head)` | pure fn | valid sig → (ct, ext) | junk/empty → None; sniff over declared |
| P6 | `PlantService.delete` (cleanup) | use case | enumerate→cascade→unlink | (covered in integration + dual-engine) |
| F1 | `uploadPhoto / fetchPhotos / setCoverPhoto / deletePhoto / photoUrl` | FE client | FormData/paths/url | `ApiError` on non-2xx |
| F2 | `postFormData<T>` | FE client | no Content-Type set | `ApiError` on non-2xx |
| F3 | `usePhotos` hook | FE hook | reload/upload→reload | 415/413 propagate with the right message |

---

## 2. Layer assignment (HoneyComb, TEST-001 / TEST-002)

- **Integration is the primary layer** (TEST-001). The real-DB slice through
  router → `PhotoService` → `SqlAlchemyPhotoRepository` → SQLAlchemy → SQLite, **plus
  the real filesystem `PhotoStorage` adapter writing into a `tmp_path`**, carries the
  bulk of coverage: every endpoint, the round-trip, cover semantics, all security
  rejects, cross-plant 404, traversal-safe naming, and the plant-delete file cleanup.
- **Unit only where integration cannot economically reach** (TEST-001 (b)) or where the
  logic is **pure** (TEST-001 (a)):
  - `sniff_image_type` is a pure stdlib function with a wide input-state matrix
    (≥6 cells, TEST-007) → **unit** is the natural home. It is *also* observed
    end-to-end through the upload endpoint, but the exhaustive matrix lives in the unit.
  - `PhotoService.upload` orchestration branches (oversize, bad-magic, mismatch,
    missing-plant, first-is-cover, delete-promotes, storage-after-repo ordering) against
    **fakes** — these prove the orchestration/ordering contract cheaply and pin the
    error-type mapping without standing up the app. The headline security behaviour is
    re-proven in integration end-to-end.
- **Dual-engine** (`test_fk_cross_engine.py`): the photo-row CASCADE on the **real
  engine** resolved from `DATABASE_URL` (the CI postgres leg proves CASCADE on both
  engines). File-cleanup is app-level → engine-agnostic → covered **once** in the SQLite
  integration suite (no dual-engine duplication).
- **Migration** (`test_migrations.py`): `0004` up/down DDL on the always-available SQLite
  path; CI runs the postgres leg.
- **Acceptance (Playwright, TEST-009): DEFERRED** to the infra story (proposal deviation
  #4), covered here by integration + the prod-path smoke + FE-012 screenshots. The
  intended journey is recorded in §10 but **not built**.

---

## 3. Backend unit: `test_photo_magic_byte_sniff.py` (`unit`)

`pytestmark = pytest.mark.unit`. Pure-function matrix for `sniff_image_type(head: bytes)
-> tuple[content_type, ext] | None`. This is the TEST-007 input-state matrix (≥6 cells,
named branch-priority order), driven by `pytest.mark.parametrize`.

### 3a. Named branch-priority order

The sniff inspects the leading bytes in a **fixed priority**; the first matching
signature wins, otherwise `None`. The implementation MUST follow and the tests MUST
assert this order:

1. **JPEG** — head starts with `FF D8 FF` → `("image/jpeg", "jpg")`.
2. **PNG** — head starts with `89 50 4E 47 0D 0A 1A 0A` → `("image/png", "png")`.
3. **WEBP** — head starts with `RIFF` (`52 49 46 46`), bytes 8..12 == `WEBP`
   (`57 45 42 50`) → `("image/webp", "webp")`.
4. **otherwise** → `None` (covers GIF, plain text, empty, truncated, RIFF-but-not-WEBP).

The sniff is **authoritative**: it inspects only the byte content. It never consults the
declared content-type or the client filename. The "declared" dimension in the matrix is
therefore exercised one layer up (the service / endpoint cross-check), and asserted here
only as *independence* (a wrong declared type cannot flip a sniff result).

### 3b. Input-state matrix — dimensions × cells

Dimensions: **{byte-signature} × {declared-context}**. Byte-signature is the primary
dimension (6 values); declared-context proves independence (2 values).

| id | head bytes (fixture) | signature | declared-context | expected | proves |
|---|---|---|---|---|---|
| `jpeg-sig` | `FF D8 FF E0 ...` | jpeg | declared `image/jpeg` (match) | `("image/jpeg","jpg")` | happy jpeg |
| `png-sig` | `89 50 4E 47 0D 0A 1A 0A ...` | png | declared `image/png` (match) | `("image/png","png")` | happy png |
| `webp-sig` | `RIFF` + size + `WEBP...` | webp | declared `image/webp` (match) | `("image/webp","webp")` | happy webp (RIFF....WEBP) |
| `gif-sig` | `47 49 46 38 39 61` (`GIF89a`) | gif (disallowed) | declared `image/gif` | `None` | disallowed type rejected at sniff |
| `plain-text` | `b"hello world ..."` | none | declared `text/plain` | `None` | junk → None |
| `empty` | `b""` | none | declared anything | `None` | empty/zero-length → None |
| `jpeg-sig-wrong-declared` | `FF D8 FF ...` | jpeg | declared `image/png` (mismatch) | `("image/jpeg","jpg")` | **sniff authoritative over a wrong declared type** |
| `png-sig-wrong-ext-declared` | `89 50 4E 47 ...` | png | filename `evil.txt` declared `application/octet-stream` | `("image/png","png")` | **sniff authoritative over a wrong extension/declared** |
| `riff-not-webp` | `RIFF` + size + `AVI ` | none | declared `image/webp` | `None` | RIFF container that is not WEBP → None (priority-3 guard) |
| `truncated-png` | `89 50 4E 47` (4 bytes only) | none | declared `image/png` | `None` | short head below the full PNG magic → None |

**Branch-priority assertions** (named, beyond the cell table):
- `test_sniff_priority_jpeg_before_others` — a JPEG head returns jpeg even when later
  signatures could theoretically be confused.
- `test_sniff_authoritative_over_declared_mismatch` — `jpeg-sig-wrong-declared` and
  `png-sig-wrong-ext-declared` confirm the function ignores the declared/extension input
  entirely (it takes only bytes; the test documents the contract that *the caller* must
  not pass declared through).
- `test_sniff_riff_requires_webp_tag` — `riff-not-webp` proves WEBP is gated on the
  `WEBP` tag at offset 8, not merely the `RIFF` prefix.

Valid signatures → `(content_type, ext)`; junk/empty/disallowed/truncated/RIFF-not-WEBP
→ `None`. **Critical (100%)**: every branch of the priority ladder is a cell above; the
`None` fall-through is the security default.

---

## 4. Backend unit: `test_photo_use_case.py` (`unit`)

`pytestmark = pytest.mark.unit`. `PhotoService.upload/list/get/set_cover/delete` against a
hand-written **fake `PhotoRepository` + fake `PhotoStorage`** (TEST-003: faking the port
is allowed; only the real persistence/storage must not be mocked in *integration*). The
fakes mirror the `_FakePlantRepository` pattern: a dict-backed repo and an in-memory
`{name: bytes}` storage that records `save`/`delete` call order.

The fake storage exposes a `saved: dict[str,bytes]` and a `calls: list[tuple]` log so the
**ordering** assertion (repo.delete before storage.delete) is observable.

### 4a. `upload` cases

| test | setup | expectation |
|---|---|---|
| `test_upload_happy_persists_and_returns_metadata` | plant exists, valid jpeg bytes within cap | returns a `Photo` with id/plant_id/content_type=`image/jpeg`/size/created_at; storage.save called once with the sniffed suffix; repo.add called with `make_cover=True` (first) |
| `test_upload_oversize_raises_photo_too_large` | bytes length > `max_bytes` | raises `PhotoTooLargeError`; storage.save **not** called; repo.add **not** called |
| `test_upload_bad_magic_raises_unsupported` | declared `image/jpeg`, body plain text / gif | raises `UnsupportedImageTypeError`; nothing persisted |
| `test_upload_declared_sniff_mismatch_rejected` | declared `image/png`, body is jpeg bytes | rejected → `UnsupportedImageTypeError` (the declared/sniff cross-check), nothing persisted |
| `test_upload_missing_plant_raises_plant_not_found` | `plant_exists` → False | raises `PlantNotFoundError`; storage.save **not** called (plant-exists is checked first) |
| `test_upload_first_photo_becomes_cover` | empty plant, one upload | repo.add called with `make_cover=True` |
| `test_upload_second_photo_not_cover` | plant already has a photo | second upload → `make_cover=False` |

**Orchestration order asserted** (P2/P5, design `application/photos.py`): the upload
pipeline is `plant-exists → size → sniff → declared/sniff cross-check → storage.save →
repo.add`. The oversize/bad-magic/mismatch/missing-plant cases each assert that
`storage.save` was **not** reached, proving the validation happens before any bytes hit
disk (no orphan files from rejected uploads).

### 4b. `delete` cases

| test | setup | expectation |
|---|---|---|
| `test_delete_promotes_newest_survivor_when_cover_removed` | 3 photos, the cover is the oldest, delete the cover | the **newest** survivor becomes cover (order_by `created_at desc`, P5) |
| `test_delete_non_cover_leaves_cover_unchanged` | delete a non-cover | the existing cover stays |
| `test_delete_last_photo_leaves_no_cover` | delete the only photo | no survivor to promote; no error |
| `test_delete_calls_storage_delete_after_repo_delete` | delete a photo | `calls` log shows repo.delete **then** storage.delete (DB first, P5/design `application/photos.py`) |
| `test_delete_missing_photo_raises` | unknown photo id | `PhotoNotFoundError` |

`get`/`set_cover` sad: `test_get_missing_raises_photo_not_found`,
`test_set_cover_missing_raises_photo_not_found`.

---

## 5. Backend integration: `test_photos_endpoint.py` (`integration`)

`pytestmark = pytest.mark.integration`. Real DB + **real filesystem storage into
`tmp_path`**, nothing internal mocked (TEST-003). Each test seeds its own plant via the
API (TEST-006 independence). Multipart via the TestClient:
`client.post(url, files={"file": ("x.jpg", JPEG_BYTES, "image/jpeg")})`.

### 5a. Fixture additions (call out for the build agent)

The merged `migrated_settings`/`client` fixture in
`backend/tests/integration/conftest.py` **must be extended**: `Settings(...)` needs a
`photos_dir` pointed at a `tmp_path` subdir (e.g. `tmp_path / "photos"`) and a small
`photos_max_bytes` is helpful for the oversize test. Today `migrated_settings` only sets
`database_url` + `version`; add `photos_dir=tmp_path / "photos"` (and optionally a low
`photos_max_bytes` so the oversize test does not need a 10 MB payload). The test module
also exposes the on-disk dir to assertions (the file-gone / UUID-name / cleanup checks
inspect `photos_dir`). Keep `tmp_path` per-test so the suite stays parallel-safe.

### 5b. Byte fixtures (module-level constants, smallest-valid)

Define minimal valid magic-byte payloads so they pass the sniff without bundling real
images (no PII, no committed binaries):
- `JPEG_BYTES` = `b"\xff\xd8\xff\xe0\x00\x10JFIF" + b"\x00" * 8`
- `PNG_BYTES` = `b"\x89PNG\r\n\x1a\n" + b"\x00" * 16`
- `WEBP_BYTES` = `b"RIFF" + (size).to_bytes(4,"little") + b"WEBPVP8 " + b"\x00" * 8`
- `GIF_BYTES` = `b"GIF89a" + b"\x00" * 8` (disallowed)
- `TEXT_BYTES` = `b"this is definitely not an image"`

### 5c. Happy inventory

| test | asserts |
|---|---|
| `test_upload_jpeg_returns_201_and_metadata` | 201; body has `id, plant_id, content_type=image/jpeg, size_bytes, is_cover=true, created_at, url`; **NO `stored_filename` key** in the body (security boundary, AC1/AC11/ARCH-007) |
| `test_upload_png_and_webp_round_trip` | png + webp each 201; content_type matches the sniff |
| `test_get_bytes_round_trips` | upload then `GET .../{id}` → 200; `response.content == JPEG_BYTES`; `Content-Type == image/jpeg`; `Cache-Control` header present (`private, max-age=31536000, immutable`, P4) |
| `test_list_newest_first` | upload three; list is ordered `created_at desc` (newest first, AC5/P5) |
| `test_first_upload_is_cover` | the first photo has `is_cover=true` (AC6) |
| `test_set_cover_flips_exactly_one` | upload two; set-cover the second → 200; exactly one `is_cover=true` across the list, the previously-covered one is now false (AC6) |
| `test_delete_then_get_404_and_file_gone` | delete → 204 (empty body); subsequent `GET .../{id}` → 404; the on-disk file is unlinked from `photos_dir` (AC7) |

### 5d. Security / sad inventory (the core of this story)

| test | input | expectation |
|---|---|---|
| `test_upload_oversize_returns_413` | body > `photos_max_bytes` | 413; id/int-only body (AC2) |
| `test_upload_declared_text_plain_returns_415` | `files={"file":("x.txt",TEXT_BYTES,"text/plain")}` | 415 (disallowed declared type, AC2) |
| `test_upload_wrong_magic_text_body_returns_415` | declared `image/jpeg`, body `TEXT_BYTES` | 415 (sniff rejects, AC2) |
| `test_upload_wrong_magic_gif_body_returns_415` | declared `image/jpeg`, body `GIF_BYTES` | 415 (disallowed sniff result, AC2) |
| `test_upload_declared_sniff_mismatch_returns_415` | declared `image/png`, body `JPEG_BYTES` | 415 (declared/sniff cross-check, AC2) |
| `test_upload_missing_plant_returns_404` | post to a non-existent plant id | 404 id-only (AC3) |
| `test_get_missing_photo_returns_404` | GET a non-existent photo on a real plant | 404 |
| `test_cover_missing_photo_returns_404` | set-cover a non-existent photo | 404 |
| `test_delete_missing_photo_returns_404` | delete a non-existent photo | 404 |
| `test_get_cross_plant_photo_returns_404` | upload to plant A; `GET /plants/{B}/photos/{A_photo}` | 404 (AC5, cross-plant isolation; no ownership model → 404 not 403) |
| `test_cover_cross_plant_returns_404` | set-cover plant A's photo via plant B's path | 404 |
| `test_delete_cross_plant_returns_404` | delete plant A's photo via plant B's path | 404 |
| `test_path_traversal_safe_naming` | client filename `"../../etc/evil.jpg"`, valid jpeg body | 201; the on-disk file is a **UUID name + `.jpg`** inside `photos_dir`; the malicious string `"etc/evil"` / `".."` appears **nowhere** under `photos_dir` (no file path, no entry) and no file escaped the dir (AC4) |
| `test_cover_promotion_on_delete` | upload three, delete the cover → the newest survivor is the new cover (AC6, end-to-end) |

### 5e. Plant-delete cleanup (P6, AC8)

| test | asserts |
|---|---|
| `test_plant_delete_cleans_photo_files` | upload N photos to a plant, capture their on-disk filenames; `DELETE /plants/{id}` → 204; the photo **rows are gone** (a fresh list/get → 404) **AND** the files are **unlinked** from `photos_dir`. This proves the app-level cleanup (`PlantService.delete` enumerates filenames → cascade rows → unlink files) actually removed the bytes, not just the rows. |

### 5f. OpenAPI assertion (TEST-008, AC11)

| test | asserts |
|---|---|
| `test_openapi_exposes_photo_paths_and_schema_omits_stored_filename` | the emitted `/api/v1/openapi.json` `paths` contain `/api/v1/plants/{plant_id}/photos` and `/api/v1/plants/{plant_id}/photos/{photo_id}` (+ `/cover`); `components.schemas.PhotoResponse.properties` keys == `{id, plant_id, content_type, size_bytes, is_cover, created_at, url}` and **does NOT contain `stored_filename`** |

### 5g. No-PII discipline (assert on every reject)

For **all 404/413/415** bodies: the JSON body keys are `{"detail"}` and the detail is
**id/int-only** — it MUST NOT echo the client filename, the body content, or any
declared header value. Add an explicit assertion to the cross-plant 404, the
missing-plant 404, the 413, and each 415 that the client filename (`"x.txt"`,
`"../../etc/evil.jpg"`) is **absent** from `response.text` (SEC-001/SEC-007). This is the
no-PII-leak critical path.

---

## 6. Dual-engine: edit `test_fk_cross_engine.py` (`integration`)

Add one test mirroring `test_deleting_a_plant_cascades_its_tag_rows`, resolving the engine
from `DATABASE_URL` via the existing `fk_engine` fixture (SQLite locally, PostgreSQL on
the CI postgres leg):

| test | asserts |
|---|---|
| `test_deleting_a_plant_cascades_its_photo_rows` | build a plant via `SqlAlchemyPlantRepository`; add ≥2 photo rows via `SqlAlchemyPhotoRepository` (a `_count_photo_rows` helper counting `PhotoModel.plant_id == plant.id`, mirroring `_count_tag_rows`); assert the count, delete the plant, assert the photo-row count is `0` (FK `ON DELETE CASCADE` fired on the **real engine**, AC8). Self-contained: cleans up its own rows; no shared postgres state. |

**Scope note:** this test proves the **DB-row CASCADE on both engines** only. File cleanup
is app-level (engine-agnostic) and is covered once by `test_plant_delete_cleans_photo_files`
in §5e — deliberately not duplicated here (the dual-engine fixture uses the repos directly,
not the storage adapter).

---

## 7. Migration: edit `test_migrations.py` (`integration`)

Mirror the existing `0003` up/down tests:

| test | asserts |
|---|---|
| `test_upgrade_creates_photo_table_and_downgrade_drops_it` | upgrade head; `inspect(engine)` shows the `photo` table with columns `{id, plant_id, stored_filename, content_type, size_bytes, is_cover, created_at}` (no `updated_at` — photos immutable, design `models.py`); the FK to `plant` is `ON DELETE CASCADE`; an index on `plant_id`; `stored_filename` is unique. Downgrade to `0003` drops `photo` but leaves `plant`/`plant_tag`. |

CI runs the same DDL on the postgres leg (no separate test needed).

---

## 8. Frontend (vitest)

Mirror `plants.test.ts` / `usePlants.test.ts`: stub `fetch` via `vi.stubGlobal`,
`okJson`/`fail` helpers, `afterEach(unstubAllGlobals + restoreAllMocks)`. **fetch is the
mock boundary** (TEST-003 FE equivalent — no MSW needed for these unit-level client/hook
tests).

### 8a. `photos.test.ts`

| test | asserts |
|---|---|
| `test uploadPhoto builds FormData field "file"` | `uploadPhoto(plantId, file)` calls `postFormData` / `fetch` with a `FormData` body whose `file` field is the given `File`; method POST; the path `/api/v1/plants/{id}/photos` |
| `test uploadPhoto does NOT set Content-Type` | the request init has **no** `Content-Type` header (the browser sets the multipart boundary; setting it manually breaks the boundary) — assert the headers object lacks `Content-Type` |
| `test fetchPhotos GETs the collection path` | `GET /api/v1/plants/{id}/photos`, `Accept: application/json` |
| `test setCoverPhoto POSTs the cover sub-resource` | `POST /api/v1/plants/{id}/photos/{photoId}/cover` |
| `test deletePhoto DELETEs the resource path` | `DELETE /api/v1/plants/{id}/photos/{photoId}`; resolves void on 204 |
| `test photoUrl builds the bytes URL` | `photoUrl(plantId, photoId) === "/api/v1/plants/{id}/photos/{photoId}"` |
| `test postFormData throws ApiError on non-2xx` | a 415/413/500 response → rejects `instanceof ApiError` (carries the status) |
| `test uploadPhoto throws ApiError on 415/413` | non-2xx upload → `ApiError` propagates |

### 8b. `usePhotos.test.ts`

| test | asserts |
|---|---|
| `test reload populates photos` | mount → fetch list → `photos` populated, `loading` false, `error` null |
| `test upload triggers a reload (mutation→reload contract)` | `upload(file)` POSTs then re-fetches the list; the new photo appears (mirrors the usePlants create→reload pattern) |
| `test setCover triggers a reload` | `setCover(id)` POSTs cover then reloads |
| `test remove triggers a reload` | `remove(id)` DELETEs then reloads |
| `test 415 propagates as ApiError with the JPEG/PNG/WebP message` | upload returns 415 → the hook surfaces `error` "only JPEG/PNG/WebP" (design `usePhotos.ts`) |
| `test 413 propagates as ApiError with the too-large message` | upload returns 413 → `error` "too large (max 10 MB)" |

---

## 9. Mocking boundary (TEST-003) — explicit

- **Integration (`test_photos_endpoint.py`):** real DB + **real `PhotoStorage` filesystem
  adapter writing into `tmp_path`**. Nothing internal mocked. This is non-negotiable for
  this story — the traversal-safe-naming and file-cleanup assertions are only meaningful
  against a real filesystem.
- **Dual-engine / migration:** real engines (SQLite local, Postgres CI), real Alembic.
- **Unit (`test_photo_use_case.py`):** fakes for `PhotoRepository` **and** `PhotoStorage`
  only (faking the port is allowed). `test_photo_magic_byte_sniff.py` mocks nothing (pure
  function).
- **Frontend (vitest):** `fetch` stubbed via `vi.stubGlobal`; no real network. `File` /
  `FormData` are the real browser/jsdom objects (the FormData-field + no-Content-Type
  assertions need the real types).

---

## 10. Playwright (TEST-009) — DEFERRED, journey recorded only

Per proposal deviation #4, the acceptance test is deferred to the infra story and **not
built here**. The intended journey, recorded so the future story can implement it
verbatim:

1. From the plants page, click the **Photos** ghost button on a plant card → the gallery
   modal opens (empty state visible when no photos).
2. Upload via `setInputFiles` on the labeled file input (a real fixture image), click
   Upload → a thumbnail appears in the grid.
3. Click **Set cover** on a thumbnail → the cover pill moves to it (exactly one cover);
   the plant card shows the cover thumbnail.
4. Upload a second image, **Delete** the first → it disappears; cover promotion is
   observable if the cover was the deleted one.
5. Delete the last photo → the empty state returns.
6. **Console-error fail-on (TEST-010):** the journey fails on any page error or
   error-level console output; warnings ignored; any allowlist needs an inline
   justification.

The driver MUST use real UI affordances (real file input, real buttons) — never inject
values directly.

---

## 11. Coverage targets (QG-002)

- **Overall floor 85%**; **new/changed code ≥80% diff-cover**.
- **Branch coverage:** **≥95% in domain + application** (`domain/photo.py` incl.
  `sniff_image_type`; `application/photos.py`; `application/plants.py` P6 path),
  **≥80% in adapters/outbound** (`photo_repository.py`, `photo_storage.py`).
- **Critical paths flagged 100%** (spec-flagged → QG-002 100%):
  1. **Upload-validation paths** — size cap → 413, content-type allowlist + magic-byte
     sniff → 415, declared/sniff mismatch → 415. Every reject branch and the "rejected
     before storage.save" guard.
  2. **404 no-PII** — every 404/413/415 reject returns an id/int-only body with no client
     filename / body / header echo (the §5g assertions).
  3. **Path-traversal-safe naming** — the on-disk name is a server UUID + sniffed ext;
     the fs adapter's resolve-within-`PHOTOS_DIR` assertion; the malicious filename never
     reaches disk.
  4. **Plant-delete cleanup** — `PlantService.delete` enumerates → cascades rows →
     unlinks files (P6), proven row-gone **and** file-gone.

The combined pytest run (unit + integration) scores the union (TEST-001); the integration
bulk plus the targeted sniff/use-case units clear the floor without brittle
implementation-mirroring units (TEST-004).

---

## 12. Required pytest markers (TEST-012)

Module-level `pytestmark` on every new/edited Python test file:
- `test_photo_magic_byte_sniff.py` → `pytestmark = pytest.mark.unit`
- `test_photo_use_case.py` → `pytestmark = pytest.mark.unit`
- `test_photos_endpoint.py` → `pytestmark = pytest.mark.integration`
- `test_fk_cross_engine.py` (edited) → already `pytestmark = pytest.mark.integration`
- `test_migrations.py` (edited) → already `pytestmark = pytest.mark.integration`

Frontend `*.test.ts` run under vitest (no marker). File-size: keep
`test_photos_endpoint.py` under the QG-009 **500-LOC hard max**; if it grows past that,
split by group (happy / security-sad / cleanup+openapi).

---

## 13. TEST-014 — Test-first evidence (the red), per lane

Test-first is **auditable from artifacts, not trusted from a claim** (TEST-014). Each lane
records, in `worklog.md`, the **failing run that precedes the implementation** — the test
names plus the failing assertion/error output (the "red") — before the commit that turns
them green:

- **Backend lane red:** run `test_photo_magic_byte_sniff.py`, `test_photo_use_case.py`,
  `test_photos_endpoint.py`, the new `test_fk_cross_engine.py::test_deleting_a_plant_cascades_its_photo_rows`,
  and the `0004` migration test against the *unimplemented* code → expect
  collection/import errors or assertion failures (no `domain.photo`, no `/photos` routes,
  no `photo` table). Capture the names + the first failing line per group.
- **Frontend lane red:** run `photos.test.ts` + `usePhotos.test.ts` against the
  *unimplemented* `lib/api/photos.ts` / `usePhotos.ts` → expect module-not-found /
  assertion failures. Capture the names + errors.

A lane whose worklog shows **no red-before-green** is a PRIN-III deviation requiring
comply-or-explain. The coverage + passing suite prove the tests exist and pass; the red
proves they were written first.

---

## 14. Re-audit note (DoD §3)

At story-complete, the test-engineer re-audits the implemented suite against this
foundation and issues the **test-foundation approval**, checking:
- Every surface in §1 has its happy + sad (TEST-005); the sniff matrix §3b and the
  service cases §4 are present and parametrized where prescribed (TEST-007).
- The four **critical-100%** paths (§11) are actually exercised end-to-end against the
  real DB + real tmp storage, not just the fakes.
- No `stored_filename` crosses any response boundary (body §5c + OpenAPI §5f), and no
  reject body echoes the client filename / content (§5g) — the security boundary holds.
- The TEST-014 red is recorded per lane (§13); the markers (§12) are present; the suite
  is parallel-safe (TEST-006) with `tmp_path`-scoped storage and per-test seeding.
- The Playwright journey (§10) remains deferred with the proposal-deviation note intact,
  and the prod-path smoke (real upload → serve → delete → cleanup) ran before merge.

Open BLOCKING gaps against this foundation block the story (QG-012); they feed the
SEC-010 end-of-feature security review.
