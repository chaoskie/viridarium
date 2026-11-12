# D-010 (ADR-010): Add `python-multipart` for file upload

Status: accepted, 2026-06-09. Amends the stack lock (`ARCH-001`).

## Context

Photo upload (US-2.3) accepts `multipart/form-data`. FastAPI and Starlette delegate
multipart parsing to the third-party `python-multipart` package; without it, a route
declaring `file: UploadFile` raises at request time. There is no standard-library path
through FastAPI.

## Decision

Add **`python-multipart`** to the backend runtime dependencies, pinned
`>=0.0.20,<0.1.0`. It is the canonical multipart parser for the Starlette ecosystem, has
no native build dependencies (safe for the Raspberry-Pi-class target in product-spec
section 7), and is covered by the existing dependency-audit gate.

**Declined: Pillow and other image libraries.** Upload validation uses a
standard-library magic-byte sniff on the first bytes. There are no server-side
thumbnails; the frontend sizes full images with CSS. This keeps the stack minimal and
avoids native dependencies. Generated thumbnails, if ever wanted for bandwidth, need
their own ADR.

## Options considered

- **Chosen:** add `python-multipart`.
- Hand-roll multipart parsing from the raw ASGI body. Rejected: more code, more risk and
  a worse security surface than a maintained library.
- Store image URLs only. Rejected: contradicts the filesystem-storage requirement in the
  product spec.

## Consequences

- `backend/pyproject.toml` and `uv.lock` carry the pinned dependency.
- The stack lock notes the amendment in
  [`rules/architecture.md`](../../rules/architecture.md).
- Upgrades are deliberate (pinned range) and reviewed like any dependency bump.
- Pillow stayed declined when the photo crop bugs came up (BUG-008, BUG-009): both were
  solved in rendering, see [testing-e2e.md](../testing-e2e.md).
