# Tasks - photos (US-2.3)

Disjoint lanes (backend G1-G5, frontend G6-G7), parallel under the orchestrator. G0 first.
TEST-014: each lane records its failing run in the worklog before the green. The dep
(`python-multipart`) is already added (ADR-010).

## G0 - Test-foundation (test-engineer)
- [ ] `test-foundation.md`: the sniff matrix, happy+sad per surface, the security rejects
      (413/415×3, cross-plant 404, traversal-safe naming), cover-promotion, plant-delete
      cleanup, dual-engine photo CASCADE, multipart test approach, coverage targets, TEST-014.

## G1 - Domain (backend)
- [ ] `domain/photo.py`: `Photo`/`NewPhoto`, errors (`PhotoNotFoundError`/`UnsupportedImageTypeError`/`PhotoTooLargeError`), `PhotoRepository` + `PhotoStorage` Protocols, pure `sniff_image_type`.
- [ ] Unit (red→green): `test_photo_magic_byte_sniff.py` (the sniff matrix).

## G2 - Application (backend)
- [ ] `application/photos.py`: `PhotoService` (upload orchestration + list/get/set_cover/delete/storage_path).
- [ ] `application/plants.py`: P6 plant-delete file cleanup (inject photo repo + storage).
- [ ] Unit (red→green): `test_photo_use_case.py` (upload happy/oversize/bad-magic/mismatch/missing-plant, first-is-cover, delete-promotes) against fake repo+storage.

## G3 - Persistence (backend)
- [ ] `models.py`: `PhotoModel`. `photo_repository.py`: `SqlAlchemyPhotoRepository` (cover invariant, promotion, cross-plant filter, `plant_exists`, `list_filenames_for_plant`).
- [ ] `photo_storage.py`: filesystem adapter (uuid naming, path-traversal guard, idempotent delete).
- [ ] `migrations/0004_create_photo.py` (down_rev 0003; FK CASCADE + indexes).
- [ ] Integration: migration `0004` up/down; extend `test_fk_cross_engine.py` with photo-row CASCADE.

## G4 - Web surface (backend)
- [ ] `schemas.py`: `PhotoResponse` (no `stored_filename`). `dependencies.py`: `get_photo_service`. `settings.py`: `photos_dir`/`photos_max_bytes`.
- [ ] `photos.py` router: upload (capped read), list, get-bytes (FileResponse + cache), set-cover, delete.
- [ ] Integration (red→green): `test_photos_endpoint.py` (AC1-AC8, AC11 + the full security matrix; `photos_dir`→tmp_path in the fixture).

## G5 - Wiring (backend)
- [ ] `container.py` (storage+repo+service; inject into PlantService) + `app.py` (router, app.state, 3 handlers).
- [ ] Gate: `make lint format-check typecheck imports test-coverage audit` (pip-audit now scans python-multipart).

## G6 - API client (frontend)
- [ ] `lib/api/client.ts`: `postFormData` (no manual Content-Type). `lib/api/photos.ts`: types + fns + `photoUrl`; `photos.test.ts`.

## G7 - Gallery (frontend)
- [ ] `features/plants/usePhotos.ts` (+ test). `PhotoGalleryModal.tsx` (grid, upload, set-cover, delete, a11y). `PlantsPage.tsx`: Photos action + cover thumbnail.
- [ ] Gate: `make fe-lint fe-format-check fe-typecheck fe-test fe-build`.

## G8 - Evidence + close (orchestrator)
- [ ] Independent full gate + live OpenAPI cross-check + **prod-path security smoke** (real upload incl. oversize/bad-magic rejects, serve bytes, set-cover, delete+file-gone, plant-delete cleans files, traversal-safe naming) + UI gallery flow.
- [ ] FE-012 screenshots; test-engineer re-audit approved; **security-focused** code-review CLEAN; DoD PASS/FAIL.
- [ ] Branch → PR → merge (green); ticket → Done + SHA; worklog complete.
