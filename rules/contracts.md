# Contracts (`API-*`)

**Enforces:** REST contract discipline for the locked stack (ARCH-001): OpenAPI as a first-class public product, version/mutability policy, and the generated-client boundary. The REST API is a **public product** - home-automation consumers integrate against it, so contract stability matters. Consumed by design work, developers, spec workflows; pairs with TEST-008 (codegen assertion) and ARCH-007/008/009 (schema layers, surfaces, anti-corruption).

---

### API-001 — OpenAPI is the contract
The OpenAPI document is FastAPI-generated from the route + Pydantic-schema definitions, and it is the contract for every REST surface exposed by us **or** consumed by us. For an exposed surface, the schema delta (paths, request/response models, status codes) is designed as part of the change before implementation and is a first-class artifact of the change. Any HTTP integration we consume without a captured contract is forbidden.
*Targets:* design work, spec-propose, scope-reviewer.

### API-002 — Generated clients, never hand-written
Where a typed client is produced from the OpenAPI document (e.g. a TypeScript client for the React app, or a published client for consumers), it is **generated** from the spec, never hand-written. Generated code is **never edited manually** and never committed with local modifications.
*Targets:* developers, code-reviewer.

### API-003 — Pinned generator versions
Any codegen tool (OpenAPI client generator, schema exporter) is **version-pinned**; upgrades are deliberate changes with regenerated output reviewed, never silent.
*Targets:* ci, developers.

### API-004 — Published API is stable (pragmatic SemVer)
The public API is a product; published behavior under `/api/v1` is stable. Changes follow SemVer intent:
- **Additive, non-breaking** change (new optional field, new endpoint) → ships under the existing major; no break for consumers.
- **Breaking/destructive** change (removed/renamed field or endpoint, type change, semantics change) → requires a **new major version** (`/api/v2`), and **design/planning mode first**: a proposal + ADR (ARCH-010) covering consumer impact and migration before any implementation is suggested.
*Targets:* design work (planning-mode trigger), spec-propose, scope-reviewer.

### API-005 — Constrained polymorphism
OpenAPI schemas SHOULD avoid free `anyOf`/`oneOf` polymorphism in public response bodies. Where polymorphism is genuinely needed, model it with a **discriminated union** (Pydantic discriminated `Union` with a literal tag field) so generated clients and consumers get a stable shape.
*Targets:* developers, code-reviewer.

### API-006 — Major version in the URL path
REST resource paths carry the major version: **`/api/v{n}/{resource}`** (e.g. `/api/v1/plants`). The URL major matches the published API major (API-004).
*Targets:* design work, developers.

### API-007 — Atomic codegen sync
A schema change and the regeneration of everything derived from it (exported OpenAPI document, any generated TypeScript/consumer client) land in the **same change**. CI fails on drift between the live schema and the committed/generated artifacts (enforced together with TEST-008).
*Targets:* developers, ci.

### API-008 — Generated-client boundary
A generated client package imports nothing from application internals, contains no UI components, and its types correspond to exactly one API surface's schemas (ARCH-008).
*Targets:* developers, code-reviewer.

### API-009 → ARCH-002
Internal (non-HTTP) contracts are domain **ports** - defined in `architecture.md`, not restated here.
