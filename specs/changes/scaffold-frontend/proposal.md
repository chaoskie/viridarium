# Proposal - scaffold-frontend

Status: applied (walking skeleton). Epic E1 (Foundation), product-spec.

## Problem / why

The repo has no frontend. E1 requires a React build alongside the FastAPI
backend, wired to `/api/v1/health`, with quality gates. We need a thin but
correct walking skeleton: app shell + health display, no plant features, so
later stories (E2-E4) build on a locked stack and a themeable token layer.

## Scope (exact, PRIN-IV)

In:

- Vite + React 18 + TypeScript (strict) project under `frontend/`, npm with a
  committed `package-lock.json`.
- Tailwind CSS with a **theme-token layer**: semantic CSS custom properties
  (`tokens.css`) consumed by the Tailwind config, so a future theme (one of the
  5 candidates in `docs/design/themes/`, decision pending) drops in by swapping
  token values only. Default token set is neutral.
- App shell: header with nav placeholders (Today, Plants, Rooms, Journal,
  Settings), a react-router route area, and a Today page that calls
  `GET /api/v1/health` through a typed fetch client and renders the status.
  `/api` proxied to `localhost:8000` in vite dev config.
- ESLint (flat, pinned) + Prettier (pinned) per `rules/frontend.md`.
- Vitest + Testing Library: a shell smoke test and a health-client test
  (mocked fetch).
- Makefile FRONTEND targets (`fe-lint`, `fe-typecheck`, `fe-test`, `fe-build`,
  `dev-frontend`). No root Makefile exists yet, so written to
  `frontend/Makefile.frontend.mk` for the orchestrator to merge.

Out (explicitly not built):

- Any plant / location / schedule / care feature (E2-E4).
- A chosen visual theme (FE-001 design-system lock is a separate decision;
  the token contract is built to receive it).
- Playwright e2e / axe a11y scans / committed design-review screenshots. The
  shell has no real UI surface yet; FE-012/FE-015 fire on feature stories. See
  Deviations.

## Stack (PRIN-V re-affirmation)

React 18.3, TypeScript 5.7 strict, Vite 6.4, Tailwind 3.4, ESLint 9 flat +
typescript-eslint 8, Prettier 3.4, Vitest 4.1 + Testing Library. All per
ARCH-001 / `rules/frontend.md`. No second UI framework (FE-001).

## Deviations (comply-or-explain, PRIN-X)

- **FE-012 (design-review screenshots) and FE-015 (a11y + perf-budget audit
  spaces) are deferred.** These are mandatory for **UI feature** stories. This
  story is infrastructure scaffolding whose only rendered surface is a static
  shell + a status line; there is no feature interaction to scan. The FE-007
  perf budget IS wired now (vite `chunkSizeWarningLimit: 300`) so the perf-space
  baseline exists; axe/Playwright land with the first real feature story (E2).
  TypeScript version is 5.7 (not the absolute latest 6.x) because the
  typescript-eslint 8 toolchain does not yet support TS 6; this is the
  current stable strict-capable line.

## Success criteria

- `npm run lint`, `npm run typecheck`, `npm run test`, `npm run build` all
  green; `npm audit` reports 0 vulnerabilities.
- Health client renders backend status on the Today page via `/api/v1/health`.
- Theme can be reskinned by editing `tokens.css` alone (documented contract).
