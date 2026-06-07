# plant-care frontend

React 18 + TypeScript (strict) + Vite + Tailwind CSS. This is the **walking
skeleton** for epic E1 (product-spec): an app shell plus a backend health
check. No plant features yet.

## Quickstart

```bash
npm install
npm run dev        # vite dev server; /api is proxied to localhost:8000
```

The dev server proxies `/api/*` to the FastAPI backend at
`http://localhost:8000` (see `vite.config.ts`). Start the backend separately.

## Scripts

| Script                 | What it does                                  |
| ---------------------- | --------------------------------------------- |
| `npm run dev`          | Vite dev server with `/api` proxy             |
| `npm run build`        | `tsc --noEmit` then `vite build`              |
| `npm run preview`      | Serve the production build locally            |
| `npm run lint`         | ESLint (flat config, type-checked rules)      |
| `npm run typecheck`    | `tsc --noEmit` under strict flags             |
| `npm run test`         | Vitest run (jsdom + Testing Library)          |
| `npm run format`       | Prettier write over `src/`                    |
| `npm run format:check` | Prettier check (CI gate)                      |

## Layout

```
src/
  components/        shared UI (AppShell, PlaceholderPage)
  features/          feature areas; MUST NOT import each other (FE-008)
    today/           the "Today" page + HealthBadge
  lib/
    api/             typed fetch client (client.ts) + endpoint modules
  styles/
    tokens.css       the theme-token contract (see below)
    index.css        Tailwind entry + base layer
```

Cross-module imports use the `@/` alias (`@/lib`, `@/components`); within a
feature, imports stay relative. ESLint enforces that a file inside
`features/<X>` cannot import `@/features/<Y>` (FE-008).

## Theme-token contract (FE-002)

The UI is themeable by **swapping token values only**. Five candidate designs
live in `docs/design/themes/`; the final choice is pending. When it lands, the
theme is applied by overriding the values in **one file** -
`src/styles/tokens.css` - with no change to component markup or the Tailwind
config.

### How it works

1. `src/styles/tokens.css` defines every literal value as a semantic CSS custom
   property on `:root` (e.g. `--color-surface`, `--color-accent`,
   `--font-display`, `--radius-card`).
2. `tailwind.config.ts` maps each token onto a Tailwind utility via
   `var(--token, fallback)` - e.g. `--color-surface` becomes the `bg-surface`
   / `text-surface` utilities.
3. Components only ever use the utilities (`bg-surface`, `text-accent`,
   `rounded-card`, `font-display`, `shadow-card`, `min-h-tap-min`). No raw hex,
   px, or font names appear in components (FE-002).

The current default token set is deliberately **neutral** (stone greys + a
restrained green accent). It is a placeholder, not a chosen design.

### Token catalogue

| Token                    | Tailwind utilities                | Meaning                                  |
| ------------------------ | --------------------------------- | ---------------------------------------- |
| `--color-surface`        | `bg-surface`, `text-surface`      | Default page / card background           |
| `--color-surface-raised` | `bg-surface-raised`               | Raised surface (header, cards)           |
| `--color-surface-sunken` | `bg-surface-sunken`               | Recessed surface (wells, inset areas)    |
| `--color-ink`            | `text-ink`                        | Primary text                             |
| `--color-ink-muted`      | `text-ink-muted`                  | Secondary / muted text                   |
| `--color-ink-inverse`    | `text-ink-inverse`                | Text on dark / accent fills              |
| `--color-accent`         | `bg-accent`, `text-accent`        | Brand / primary interactive             |
| `--color-accent-strong`  | `text-accent-strong`              | Stronger accent (hover, headings)        |
| `--color-accent-soft`    | `bg-accent-soft`                  | Tinted accent background (active nav)     |
| `--color-danger`         | `text-danger`, `bg-danger`        | Destructive / error state                |
| `--color-warning`        | `text-warning`                    | Caution state (e.g. overdue soon)        |
| `--color-success`        | `text-success`                    | Healthy / done state                     |
| `--color-border`         | `border-border`                   | Hairlines, dividers, control borders     |
| `--color-ring`           | `ring-ring`                       | Focus ring                               |
| `--font-display`         | `font-display`                    | Headings / brand                         |
| `--font-body`            | `font-body`                       | Body copy                                |
| `--font-mono`            | `font-mono`                       | Code / IDs / timestamps                  |
| `--radius-card`          | `rounded-card`                    | Card corner radius                       |
| `--radius-control`       | `rounded-control`                 | Buttons, inputs, nav items               |
| `--radius-pill`          | `rounded-pill`                    | Pills / badges                           |
| `--shadow-card`          | `shadow-card`                     | Resting card elevation                   |
| `--shadow-raised`        | `shadow-raised`                   | Raised / floating elevation              |
| `--size-tap-min`         | `min-h-tap-min`, `min-w-tap-min`  | 44px minimum tap target (FE-011)         |

### Adding a token

A **new** token name (new color, new shadow primitive used 3+ times, new
typeface, new structural archetype) is a **design decision** and requires an
ADR (FE-010), not developer discretion. New _combinations_ of existing tokens
are normal dev work.

### Applying a candidate theme later

Override the values in `tokens.css`. To support runtime theme switching,
mirror the `:root` block under a `[data-theme="<name>"]` selector and set the
attribute on `<html>`; the contract (token names + Tailwind mapping) does not
change.
