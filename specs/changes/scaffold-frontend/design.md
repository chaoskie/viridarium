# Design - scaffold-frontend

## Token layer (the load-bearing decision)

Two-layer indirection so a theme swap touches one file:

```
component markup        tailwind.config.ts            src/styles/tokens.css
  bg-surface     ──►  surface: var(--color-surface)  ──►  --color-surface: #fff
  text-accent    ──►  accent:  var(--color-accent)   ──►  --color-accent:  #15803d
  rounded-card   ──►  card:    var(--radius-card)     ──►  --radius-card:   0.75rem
```

- **tokens.css** holds every literal value as a semantic CSS custom property on
  `:root`. This is the only place hex / px / font names live.
- **tailwind.config.ts** maps each token to a utility via a `var(--token,
  fallback)` helper. The fallback degrades loudly-but-safely if a token is
  removed.
- **Components** use only Tailwind utilities. No raw values (FE-002).

Names are semantic (`surface`, `ink`, `accent`, `danger`), not literal
(`green`, `stone-100`), so the 5 candidate themes - each with its own bespoke
palette names (herbarium "moss/rust", terracotta "clay/sage", etc.) - map onto
the same contract by value substitution. Runtime switching is supported later by
mirroring `:root` under `[data-theme="..."]` without contract changes.

The default token set is neutral (stone greys + restrained green) and is
explicitly a placeholder, not a chosen design (FE-001 lock is pending).

## Module layout & boundaries (FE-008)

```
src/components/   shared, cross-feature UI (AppShell, PlaceholderPage)
src/features/X/   isolated feature areas (today/)
src/lib/api/      typed API client (shared)
src/styles/       tokens + Tailwind entry
```

Cross-module imports use the `@/` alias (tsconfig `paths` + vite
`resolve.alias`). FE-008 is enforced by an ESLint `no-restricted-imports`
override scoped to `src/features/**`: those files may not import
`@/features/*`. The composition root (`App.tsx`, outside `features/`) freely
mounts features - that is the router's job, not a cross-feature dependency.
Negative-tested: a probe importing a sibling feature errors as expected.

## API client

`lib/api/client.ts` exposes `getJson<T>(path)` against base `/api/v1` and an
`ApiError` for non-2xx. `lib/api/health.ts` adds `fetchHealth(): HealthStatus`.
No runtime schema validation in the skeleton (no schemas exist yet); typed at
the boundary via the caller-supplied generic. Dev requests hit `/api`, proxied
to `localhost:8000` (vite).

`HealthBadge` uses a discriminated-union state (`loading | ok | error`) and an
`active` guard in `useEffect` cleanup to avoid setting state after unmount
(FE-005). `aria-live="polite"` announces the status change (FE-011).

## TypeScript strictness (FE-004)

`strict` plus `noUncheckedIndexedAccess`, `exactOptionalPropertyTypes`,
`noUnusedLocals/Parameters`. ESLint bans `any`, `object`, `{}`
(`no-explicit-any` + `no-restricted-types`). No `any` appears in the source.

## Testing

Vitest + jsdom + Testing Library. Two files:

- `App.test.tsx` - smoke: renders the shell, asserts all 5 nav links and the
  Today heading + health badge (fetch stubbed).
- `lib/api/health.test.ts` - happy (200 -> parsed body), endpoint-path
  assertion, sad (503 -> `ApiError`). Mocked `fetch` via `vi.stubGlobal`.

## Gates / CI surface

`Makefile.frontend.mk` provides `fe-lint`, `fe-typecheck`, `fe-test`,
`fe-build`, `dev-frontend`, `fe-install`, mirroring QG-001 (eslint + tsc) plus
build/test. To be merged into the root Makefile by the orchestrator.
