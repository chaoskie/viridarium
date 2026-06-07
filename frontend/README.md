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

The UI is themeable by **swapping token values only**. Two themes ship today,
both selected from the candidate designs in `docs/design/themes/`:

- **Terracotta** (`docs/design/themes/theme-04-terracotta.html`) - the
  **default**. Warm clay: cream + dot-grid background, terracotta / sage /
  mustard accents, chocolate ink, chunky 3px borders, hard-offset shadows,
  sticker-like rounded shapes, Baloo 2 display + Atkinson Hyperlegible body.
- **Herbarium** (`docs/design/themes/theme-01-herbarium.html`) - the secondary
  "cleaner view". Botanical editorial: paper cream + ruled-paper texture,
  hairline borders, muted moss / rust / gold, soft engraved-plate shadows,
  squared corners, Fraunces display + Spectral body + IBM Plex Mono labels.

A theme is applied by setting `data-theme` on `<html>`; the token VALUES are
overridden per theme in **one file** - `src/styles/tokens.css` - with no change
to component markup or the Tailwind config.

### How it works

1. `src/styles/tokens.css` defines every literal value as a semantic CSS custom
   property. `:root` and `[data-theme="terracotta"]` carry the **default**
   (Terracotta) values; `[data-theme="herbarium"]` re-binds the same token
   NAMES to the Herbarium values.
2. `tailwind.config.ts` maps each token onto a Tailwind utility via
   `var(--token, fallback)` - e.g. `--color-surface` becomes the `bg-surface`
   / `text-surface` utilities.
3. Components only ever use the utilities (`bg-surface`, `text-accent`,
   `rounded-card`, `font-display`, `font-label`, `shadow-card`, `border-card`,
   `min-h-tap-min`). No raw hex, px, or font names appear in components
   (FE-002).
4. The active theme is chosen at runtime by the **theme controller**
   (`src/lib/theme/`): an inline script in `index.html` reads
   `localStorage["plant-care.theme"]` and sets `data-theme` before first paint
   (no flash); the typed `useTheme()` hook + the `ThemeToggle` control in the
   app-shell header let the user switch. Default is `terracotta`.

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
| `--color-accent-2`       | `bg-accent-2`, `text-accent-2`    | Secondary accent (sage / moss)           |
| `--color-accent-2-strong`| `text-accent-2-strong`            | Stronger secondary accent (hover)        |
| `--color-accent-3`       | `bg-accent-3`, `text-accent-3`    | Tertiary accent (mustard / gold)         |
| `--color-danger`         | `text-danger`, `bg-danger`        | Destructive / error state                |
| `--color-warning`        | `text-warning`                    | Caution state (e.g. overdue soon)        |
| `--color-success`        | `text-success`                    | Healthy / done state                     |
| `--color-border`         | `border-border`                   | Hairlines, dividers, control borders     |
| `--color-ring`           | `ring-ring`                       | Focus ring                               |
| `--font-display`         | `font-display`                    | Headings / brand                         |
| `--font-body`            | `font-body`                       | Body copy                                |
| `--font-label`           | `font-label`                      | Uppercase / tracked micro-labels         |
| `--font-mono`            | `font-mono`                       | Code / IDs / timestamps                  |
| `--radius-card`          | `rounded-card`                    | Card corner radius                       |
| `--radius-control`       | `rounded-control`                 | Buttons, inputs, nav items               |
| `--radius-pill`          | `rounded-pill`                    | Pills / badges                           |
| `--border-width-card`    | `border-card`                     | Card / structural border weight          |
| `--border-width-control` | `border-control`                  | Control / nav border weight              |
| `--shadow-card`          | `shadow-card`                     | Resting card elevation                   |
| `--shadow-raised`        | `shadow-raised`                   | Raised / floating elevation              |
| `--bg-texture`           | (body `background-image`)         | Decorative page texture (dots / rules)   |
| `--bg-texture-size`      | (body `background-size`)          | Tile size for the texture                |
| `--size-tap-min`         | `min-h-tap-min`, `min-w-tap-min`  | 44px minimum tap target (FE-011)         |

`--bg-texture` / `--bg-texture-size` are consumed directly in the `index.css`
base layer (a multi-stop `background-image` does not map to a single Tailwind
utility), not via a generated class.

### Adding a token

A **new** token name (new color, new shadow primitive used 3+ times, new
typeface, new structural archetype) is a **design decision** and requires an
ADR (FE-010), not developer discretion. New _combinations_ of existing tokens
are normal dev work.

### Adding a third theme (recipe)

Re-binding existing token NAMES to a new palette is normal dev work (no ADR);
adding a brand-new token NAME is a design decision (FE-010). To add a theme:

1. **tokens.css** - add a `[data-theme="<name>"]` block that overrides every
   token the other themes set (copy a block, swap values). Set `--bg-texture`
   to `none` if the theme has no texture. Do not introduce new token names.
2. **themeController.ts** (`src/lib/theme/`) - add `"<name>"` to the `THEMES`
   tuple and a label to `THEME_LABELS`. `Theme`, the guard, the cycle, and the
   default all derive from these, so nothing else in the controller changes.
3. **index.html** - add `"<name>"` to the inline pre-paint script's `THEMES`
   array (keep it in sync with the controller, or the first paint can flash).
4. **fonts** - if the theme needs new typefaces, add them to the Google Fonts
   `<link>` in `index.html` (and to the self-hosting follow-up).
5. The `ThemeToggle` control and `useTheme()` hook pick up the new theme
   automatically from `THEMES`; no component markup changes.

No change to `tailwind.config.ts` or any component is needed - the contract
(token names + Tailwind mapping) is stable.
