# Design - photos (US-2.3)

New `Photo` aggregate; mirrors the plant/location [TEMPLATE]. Security-sensitive.

## Decisions

- **P1 storage:** DB stores metadata, disk stores bytes under a UUID name. `PhotoStorage`
  port (domain) + filesystem adapter (`PHOTOS_DIR`, default `/data/photos`). FK `ON DELETE CASCADE`.
- **P2 validation (security):** content-type allowlist (jpeg/png/webp) + **authoritative
  stdlib magic-byte sniff** (first ~16 bytes) + server-side size cap (capped read → 413).
  Sniff wins over the declared type/filename. Reject → 415; mismatch → 415.
- **P3 dep:** `python-multipart` added (ADR-010, approved). **No Pillow** (stdlib sniff, no thumbnails).
- **P4 serving:** `GET .../photos/{id}` via `FileResponse` with the stored content-type +
  `Cache-Control: private, max-age=31536000, immutable`; NOT a static mount. `mount_spa` last (no shadow).
- **P5 cover/delete:** first upload → cover; `set-cover` clears others in-tx; delete removes
  row+file and promotes newest survivor if the cover was deleted. Order by `created_at desc`.
- **P6 plant-delete cleanup:** `PlantService.delete` enumerates filenames (rows still present)
  → delete plant (rows cascade) → unlink files via storage (idempotent). App-level, engine-agnostic.

## REST / OpenAPI delta (`/api/v1/plants/{plant_id}/photos`, tag `photos`)

| Method | Path | Req | Success | Errors |
|---|---|---|---|---|
| POST | `` (multipart `file`) | UploadFile | 201 PhotoResponse | 404 plant, 415 type/magic, 413 oversize, 422 no-file |
| GET | `` | - | 200 list[PhotoResponse] (newest-first) | 404 plant |
| GET | `/{photo_id}` | - | 200 raw bytes (FileResponse, content-type + cache) | 404 plant/photo/mismatch |
| POST | `/{photo_id}/cover` | empty | 200 PhotoResponse | 404 |
| DELETE | `/{photo_id}` | - | 204 | 404 |

`PhotoResponse`: `id, plant_id, content_type, size_bytes, is_cover, created_at, url` (computed
`/api/v1/plants/{plant_id}/photos/{id}`). **Omits `stored_filename`** (security boundary, ARCH-007).

## Backend file plan

**New:** `domain/photo.py` (`Photo`/`NewPhoto` dataclasses; `PhotoNotFoundError`,
`UnsupportedImageTypeError`→415, `PhotoTooLargeError`→413; `PhotoRepository` Protocol
[`add(new,*,make_cover)`,`list_for_plant`,`get(plant_id,photo_id)`,`set_cover`,`delete`→returns row,
`plant_exists`,`list_filenames_for_plant`]; `PhotoStorage` Protocol [`save(data,*,suffix)->name`,
`open_path(name)->Path`,`delete(name)`]; pure `sniff_image_type(head)->(content_type,ext)|None`).
`application/photos.py` (`PhotoService(repo, storage, max_bytes)` — `upload` orchestrates
plant-exists→size→sniff→declared/sniff cross-check→storage.save→repo.add(make_cover=first);
`list/get/set_cover/delete`(repo.delete then storage.delete — DB first); `storage_path` for the route).
`adapters/outbound/db/photo_repository.py` (`SqlAlchemyPhotoRepository`, session-per-call,
`_to_domain`, single-cover invariant in-tx, cover-promotion on delete, cross-plant filter).
`adapters/outbound/db/photo_storage.py` (filesystem adapter: `mkdir exist_ok`; `save`=uuid4 hex+suffix,
write; `open_path` resolves + asserts within `PHOTOS_DIR`; `delete` unlink missing_ok).
`migrations/versions/0004_create_photo.py` (down_rev 0003; `photo` table, `pk_photo`,
`fk_photo_plant_id_plant` CASCADE, `ix_photo_plant_id`, unique `stored_filename`).
`adapters/inbound/web/photos.py` (router prefix `/plants/{plant_id}/photos`; capped read for size;
FileResponse for bytes).

**Edit:** `models.py` (+`PhotoModel`: id, plant_id FK CASCADE+index, stored_filename String(255)
unique, content_type String(64), size_bytes Integer, is_cover Boolean server_default false,
created_at; no updated_at — photos immutable). `schemas.py` (+`PhotoResponse` + `from_domain(photo, plant_id)`).
`dependencies.py` (+`get_photo_service`). `settings.py` (+`photos_dir`, `photos_max_bytes`).
`container.py` (+storage+repo+service; inject photo repo+storage into `PlantService` for P6).
`app.py` (+photos router, +`app.state.photo_service`, +handlers `PhotoNotFoundError`→404,
`UnsupportedImageTypeError`→415, `PhotoTooLargeError`→413). `application/plants.py` (P6 cleanup in `delete`).

## Frontend file plan

`lib/api/client.ts` (+`postFormData<T>(path, form)` — no manual Content-Type; browser sets boundary).
`lib/api/photos.ts` (`Photo` iface; `fetchPhotos`/`uploadPhoto(File)`/`setCoverPhoto`/`deletePhoto`/`photoUrl`).
`features/plants/usePhotos.ts` (hook: photos/loading/error + reload/upload/setCover/remove; 415→"only JPEG/PNG/WebP", 413→"too large (max 10 MB)").
`features/plants/PhotoGalleryModal.tsx` (Modal: thumbnail grid `img object-cover`, cover pill, per-thumb Set-cover/Delete, labeled file input `accept=image/*` + Upload button; a11y). `PlantsPage.tsx` (+`{kind:"photos"}` modal state, a "Photos" ghost button per card, a cover thumbnail). No new UI primitive (FE-010).

## ADR delta

- ADR-010 (D-010): add `python-multipart` (accepted). Stored-bytes via a `PhotoStorage` port
  (filesystem adapter) is the template for future blob storage. Validation-by-sniff (server
  authoritative) is the upload-security convention.

## Test seed → test-foundation

Unit: `sniff_image_type` matrix (jpeg/png/webp/gif/text/empty × declared match/mismatch);
`PhotoService.upload` (happy, oversize→413, bad-magic→415, mismatch→415, missing-plant→404,
first-is-cover, delete-promotes). Integration (real DB + tmp `photos_dir`, multipart via
TestClient `files=`): upload 201 + bytes round-trip (+cache header), list newest-first,
set-cover single, delete 204+file-gone+GET-404, all the security rejects (413/415×3), cross-plant
404, **path-traversal-safe naming** (UUID on disk, malicious filename absent), cover-promotion,
**plant-delete cleans files**, OpenAPI assertion (no `stored_filename`). Dual-engine: extend
`test_fk_cross_engine.py` with photo-row CASCADE. Migration `0004` up/down. Frontend: `photos.ts`
(FormData built, no Content-Type set; paths; ApiError), `usePhotos` (reload/upload/415-413 propagate).
TEST-014 red per lane.

## Sizing / delivery

ONE story, two parallel lanes (backend ~600 LOC — over the ~500 per-lane soft cap,
comply-or-explain per proposal #2; under the 1000 hard ceiling; ~8 small modules each <250;
frontend ~400-450). backend/ vs frontend/ disjoint; the one cross-lane touch is
`application/plants.py` (P6) which is backend. FE builds against §1; orchestrator runs a
**security-focused** code review + a prod-path smoke (real upload, serve, delete, cleanup) before merge.
