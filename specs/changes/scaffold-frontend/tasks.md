# Tasks - scaffold-frontend

- [x] T1 Scaffold Vite + React 18 + TS strict project under `frontend/`; npm,
      committed `package-lock.json`; `engines.node >= 20.19`.
- [x] T2 Strict `tsconfig.json` (strict + noUncheckedIndexedAccess +
      exactOptionalPropertyTypes + unused checks); `@/` path alias.
- [x] T3 Theme-token layer: `src/styles/tokens.css` (neutral semantic tokens)
      consumed by `tailwind.config.ts` via `var(--token, fallback)`.
- [x] T4 Tailwind + PostCSS + Autoprefixer wired; `index.css` base layer.
- [x] T5 Typed API client (`lib/api/client.ts` + `health.ts`); `/api` proxied
      to `localhost:8000` in `vite.config.ts`.
- [x] T6 App shell (`AppShell`) with header + 5 nav placeholders; react-router
      route area; Today page rendering `GET /api/v1/health`; placeholder pages.
- [x] T7 ESLint flat config (pinned) with FE-004 type bans + FE-008
      feature-isolation boundary; Prettier (pinned). Negative-tested FE-008.
- [x] T8 Vitest + Testing Library: shell smoke test + health-client test
      (mocked fetch, happy + sad + path).
- [x] T9 `Makefile.frontend.mk` with fe-lint / fe-typecheck / fe-test /
      fe-build / dev-frontend (no root Makefile to merge into yet).
- [x] T10 `frontend/README.md` documenting the token contract.
- [x] T11 Spec artifacts (proposal / design / tasks / worklog).
- [x] T12 Run all gates green; resolve npm audit to 0 vulnerabilities.

## Follow-ups (not this story)

- Orchestrator: merge `frontend/Makefile.frontend.mk` into the root Makefile
  when it is created, then delete the fragment.
- E2 (first feature story): add Playwright POM + axe a11y scan (FE-015) and a
  CI perf-budget assertion (FE-007 as a hard test, not just a build warning),
  plus committed design-review screenshots (FE-012).
- Apply the chosen theme to `tokens.css` once FE-001 design-system lock lands.
