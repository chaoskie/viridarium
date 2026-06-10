# Proposal - photos (US-2.3)

Status: applied (PR open, pending merge). Epic E2 (Plant inventory), US-2.3, high priority (project board).
The most complex E2 story; security-sensitive (file upload). New `Photo` aggregate.

## Story (SPEC-004)

> As a plant owner, I want to upload photos of each plant, see them in a gallery, pick a
> cover, and delete ones I don't want, so that I have a visual record of each plant that
> survives restarts.

## Scope (exact, PRIN-IV)

**In:**
- `Photo` domain entity + `PhotoRepository` port + `PhotoStorage` port + a stdlib
  magic-byte image sniffer (pure domain). `SqlAlchemyPhotoRepository` + a filesystem
  `PhotoStorage` adapter (configurable `PHOTOS_DIR`, default `/data/photos`, volume-mounted
  per NFR §7). `PhotoModel` + Alembic `0004` (`photo` table, FK to plant `ON DELETE CASCADE`).
- Endpoints under `/api/v1/plants/{id}/photos`: **upload** (multipart `UploadFile`, 201),
  **list** (200), **get-bytes** (`FileResponse`, correct content-type + cache headers, served
  via the API not a static mount), **set-cover** (200), **delete** (204).
- Upload validation (security): content-type allowlist (jpeg/png/webp) + **authoritative
  magic-byte sniff** + server-side size cap (`PHOTOS_MAX_BYTES`, default 10 MB). Stored under
  a server-generated UUID name + sniffed extension (never the client filename). Cross-plant
  photo access → 404.
- Cover semantics: first upload becomes cover; `set-cover` enforces a single cover; deleting
  the cover promotes the newest survivor.
- **Plant-delete file cleanup:** `PlantService.delete` enumerates the plant's photo filenames
  and unlinks them via the storage port (the DB CASCADE removes rows only).
- Frontend: a "Photos" gallery modal opened from the plant card (upload, thumbnail grid,
  set-cover, delete) + a cover thumbnail on the card; a `FormData` multipart client helper.
- Unit + integration tests incl. the security validations, cover-promotion, plant-delete
  cleanup, dual-engine photo CASCADE; FE-012 screenshots; TEST-014 red-runs.

**Out (YAGNI / SPEC-001):**
- **Pillow / image libs / server-side thumbnails** (declined, ADR-010 — stdlib validation, FE
  sizes full images via CSS).
- Drag-reorder (order by `created_at` desc; cover is the explicit selection).
- A plant detail page (US-4.3) — the gallery is a modal for now.
- Generated client (API-002): the hand-written `photos.ts` mirrors the existing hand-written
  client; API-002's "generated client" is a pre-existing repo-wide interpretation, not US-2.3's
  to resolve.

## Stack amendment (PRIN-V / ARCH-001) — APPROVED

Adds **`python-multipart`** (pinned `>=0.0.20,<0.1.0`, resolved 0.0.32) — FastAPI's required
and only multipart parser; no stdlib alternative. **Maintainer-approved 2026-06-09**, recorded
as **ADR-010** (D-010) and noted in `rules/architecture.md` ARCH-001. pip-audit/SEC-009 scans it.

## Security (PRIN-II / SEC-*, the core of this story)

- Never trust the client content-type or filename. The **magic-byte sniff is authoritative**
  for the stored content-type + extension; the client filename is never persisted or echoed
  (no PII, SEC-001/SEC-007).
- Stored name = server-generated UUID + sniffed ext → path-traversal-proof; the fs adapter also
  asserts the resolved path stays within `PHOTOS_DIR` (belt-and-suspenders).
- Size cap enforced server-side via a capped read (413), independent of any client limit.
- Cross-plant photo reference → 404 (no ownership model in v1, SEC-002).
- Images served through the API + global security middleware (`X-Content-Type-Options: nosniff`,
  SEC-011), NOT a static mount → no directory listing, no MIME-sniff-to-executable. `mount_spa`
  stays last and cannot shadow `/api/v1/*`.
- Error bodies carry ints only. **SEC-008 structured event logging is NOT implemented** here
  (corrected post-review): no CRUD route in the project emits structured events yet, so adding
  it only for photos would be inconsistent. Tracked as a repo-wide tech-debt item; consistent
  with US-2.1/2.2/2.4 which also merged without it. **Body-size limit (defense-in-depth):** the
  capped read bounds RAM, but the multipart body is spooled to disk before the size check; an
  early Content-Length / body-size-middleware guard is tracked as security tech-debt (low risk
  under the trusted-network no-auth posture, SEC-003).

## Architecture (DoR §7)

New `Photo` aggregate in the inventory context (ARCH-002); a `PhotoStorage` port keeps
filesystem I/O at the adapter boundary (ARCH-009). Dual-engine portable (ARCH-011): portable
columns, FK CASCADE (rows) covered by the cross-engine test; file cleanup is application-level
(engine-agnostic). Three-layer schemas; `stored_filename` never crosses the response boundary.

## Deviations (comply-or-explain, PRIN-X)

1. **Stack amendment** (python-multipart) — approved, ADR-010 (above).
2. **Backend lane over the ~500 per-lane soft budget** (~600 LOC). Delivered as ONE
   user-meaningful story ("photos") across parallel backend/frontend lanes, with a dedicated
   **security-focused code review** as the single tractable review unit. 1000 LOC hard ceiling
   per story NOT breached; each backend file is under the QG-009 250-LOC soft ceiling (the lane
   is ~8 small modules). The architect's 2-PR split was considered and declined for cohesion +
   momentum; recorded here. Maintainer-directed ("knock out 2.3").
3. **API-002 hand-written client** — pre-existing repo pattern, not introduced here.
4. **FE-015 Audit Spaces + TEST-009 Playwright** deferred to the infra story (unchanged);
   covered by integration (incl. the security matrix) + the prod-path smoke + FE-012 screenshots.

## Definition of Ready (QG-011)

1. Approved - PASS (PO directed "knock out 2.3"; the dep amendment explicitly approved).
2. Story format - PASS. 3. Sized - PASS-with-deviation (#2; under the hard ceiling). 4. Testable ACs - PASS (below).
5. Dependencies - PASS (new dep approved; couples to US-2.1 plant-delete for cleanup). 6. Logging/trust - PASS (no PII in errors/metadata; SEC-008 structured logging deferred repo-wide, tracked - see Security section).
7. Architecture - PASS (new aggregate, ports, dual-engine). 8. Estimate/roles - PASS (architect done; test-engineer; backend + frontend lanes; orchestrator gates+merge).
9. Contract impact - PASS (additive endpoints; multipart surface). 10. Test-foundation - PASS (scheduled). 11. Worklog - PASS.

**DoR verdict: PASS** (deviations 1-4 recorded; #1 maintainer-approved).

## Acceptance criteria

- AC1: Upload a valid JPEG/PNG/WebP → 201 + photo metadata (no `stored_filename` in the body); the bytes round-trip via GET with the correct content-type.
- AC2: Upload rejected — oversize → 413; disallowed declared type → 415; wrong magic bytes (declared image, body not) → 415; declared/sniff mismatch → 415.
- AC3: Upload to a non-existent plant → 404 (id-only, no PII).
- AC4: The stored file on disk has a UUID name + sniffed extension; a malicious client filename (`../../etc/evil.jpg`) never appears on disk and the file stays within `PHOTOS_DIR`.
- AC5: List returns the plant's photos newest-first; cross-plant photo access (plant B's path, plant A's photo) → 404.
- AC6: First upload is the cover; `set-cover` makes exactly one photo the cover; deleting the cover promotes the newest survivor.
- AC7: Delete → 204; the DB row and the file are both gone (subsequent GET → 404).
- AC8: Deleting a **plant** removes its photo rows (CASCADE, both engines) AND unlinks its photo files.
- AC9: Migrations `0004` apply + roll back on both engines.
- AC10: The plant card has a Photos action opening a gallery modal (upload / set-cover / delete) and shows the cover thumbnail; a11y honored.
- AC11: OpenAPI exposes the photo endpoints; `PhotoResponse` omits `stored_filename`.
