# Worklog - photos (US-2.3)

Per-change trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.
Public-repo hygiene: story ids only, no tracker UUIDs/hostnames.

## AI logging guidance (`TRACE-004`)
Log forks/design decisions, gate-checks, the TEST-014 red-run per lane, review verdicts,
commits, lifecycle transitions, comply-or-explain deviations. Not routine edits/reads.

---

## Entries

- `~22:35 · orchestrator/HIGH · DoD gate PASS; ready to PR · templates/dod.md · QG-012`
- `~22:33 · orchestrator/HIGH · review MEDIUM/LOW -> TD (body-size/disk-fill guard [security], SEC-008 logging repo-wide, PlantsPage size, CoverThumb N+1); corrected the proposal's over-claimed SEC-008 (logging deferred repo-wide, honest record) · proposal.md + project board · REV-003`
- `~22:30 · code-reviewer/HIGH · security review VERDICT: CLEAN (no CRITICAL/HIGH; sniff authoritative, traversal guard empirically verified, no-PII, cross-plant 404, P6 cleanup sound, scope clean); 2 MEDIUM + 2 LOW tech-debt · backend/ + frontend/ · REV-008/SEC-*`
- `~22:28 · test-engineer/HIGH · re-audit VERDICT: APPROVED (DoD §3); 194 tests 99.28%, 4 critical security paths ~100%, PhotoResponse omits stored_filename verified body+OpenAPI+source · test-foundation.md · SPEC-003`
- `~22:20 · orchestrator/HIGH · re-audit + security-focused code-review launched (DoD §2/§3) · backend/ + frontend/ · REV-008/SPEC-003`
- `~22:18 · orchestrator/HIGH · SECURITY prod-path smoke PASS (8140): valid upload 201 (cover, NO stored_filename leak), bytes round-trip (image/png + immutable cache + nosniff, identical), oversize 413, bad-magic 415, traversal-safe (UUID on disk, no evil file), cross-plant 404, plant-delete cleaned files (2->0); UI gallery: cover thumb on card, modal grid w/ Cover pill + Set-cover/Delete + upload, only pre-existing CSP errors; FE-012 screenshots committed · screenshots/ · DoD §3 prod-path/SEC-*`
- `~22:14 · orchestrator/HIGH · independent full gate PASS (backend 194/99.28% + frontend 113); live OpenAPI photo paths + PhotoResponse(no stored_filename) match the typed client; ownership clean; pip-audit scans python-multipart (no vulns) · - · QG-001/API-001`
- `~22:10 · frontend/HIGH · lane green: 113 vitest (+19); TEST-014 red recorded; postFormData (no Content-Type), photos.ts, usePhotos, PhotoGalleryModal, per-card lazy CoverThumb; no new primitive · frontend/ · QG-004/TEST-014`
- `~21:55 · backend/HIGH · GREEN: implemented domain/photo.py (Photo/NewPhoto, 3 typed errors, PhotoRepository+PhotoStorage ports, authoritative sniff_image_type) + application/photos.py (upload pipeline plant-exists->size->sniff->declared/sniff cross-check->save->add; delete DB-first) + photo_repository.py (single-cover invariant + cover-promotion) + photo_storage.py (UUID naming + resolve-within-root traversal guard + idempotent delete) + 0004 migration + PhotoModel + PhotoResponse (omits stored_filename) + photos router (capped read->413, FileResponse+cache) + settings/container/app wiring + P6 PlantService.delete file cleanup. Gates: lint/format/typecheck(strict)/imports/test-coverage(99.28%, domain+app 100%)/audit all PASS; 194 tests pass. Added test_photo_storage.py for the traversal-guard critical path · backend/ · TEST-014/PRIN-III`
- `~21:20 · backend/HIGH · TEST-014 RED (test-first, before impl): wrote test_photo_magic_byte_sniff.py + test_photo_use_case.py + test_photos_endpoint.py + extended test_fk_cross_engine.py (test_deleting_a_plant_cascades_its_photo_rows) + test_migrations.py (0004 photo table) + conftest photos_dir/photos_max_bytes; ran the lot against unimplemented code -> ImportError: cannot import name 'PhotoModel' from ...db.models (collection errors: no domain.photo, no photo_repository, no /photos routes, no photo table). Red recorded -> implementing to green · backend/tests · TEST-014/PRIN-III`
- `~21:05 · orchestrator/HIGH · build fan-out launched: backend + frontend lanes (disjoint, test-first, TEST-014) · backend/ + frontend/ · PRIN-VI`
- `~21:03 · test-engineer/HIGH · test-foundation authored: sniff matrix + ~21 integration (7 happy/14 security-sad) + dual-engine CASCADE + migration; 4 critical-100% paths (upload-validation, 404 no-PII, traversal-safe naming, plant-delete cleanup) · test-foundation.md · SPEC-003`
- `~20:48 · test-engineer/HIGH · test-foundation pass launched (G0): security matrix first-class · test-foundation.md · SPEC-003`
- `~20:47 · orchestrator/HIGH · DoR PASS; spec authored (proposal/design/tasks); kept as ONE PR (backend lane ~600 LOC comply-or-explain, security-focused review) vs the architect's 2-PR split · specs/changes/photos · QG-011/SPEC-002`
- `~20:46 · Lars (PO) + orchestrator/HIGH · STACK AMENDMENT approved: add python-multipart (pinned >=0.0.20,<0.1.0, resolved 0.0.32); ADR-010 written; ARCH-001 noted; Pillow declined (stdlib magic-byte sniff) · pyproject.toml + D-010 + rules/architecture.md · PRIN-V/ARCH-001/ARCH-010`
- `~20:45 · architect/HIGH · design returned: Photo aggregate + PhotoStorage port + fs adapter; magic-byte sniff (authoritative); UUID stored names (traversal-safe); FileResponse serving; cover invariant; plant-delete file cleanup (P6); the python-multipart finding · design.md · -`
- `~20:45 · architect/HIGH · US-2.3 architect pass launched (Photo entity + filesystem storage + multipart upload + serving + cover/gallery; security-sensitive; dep + file-cleanup decisions) · - · sprint`
- `~20:44 · orchestrator/HIGH · US-2.3 picked up: Todo -> In Progress + comment; branched feat/us-2.3-photos off main (US-2.4 #18 merged) · git/board · PRIN-VI`
- `~20:44 · orchestrator/HIGH · change opened · specs/changes/photos/ · SPEC-002`
