# Viridarium frontend

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

| Script                 | What it does                             |
| ---------------------- | ---------------------------------------- |
| `npm run dev`          | Vite dev server with `/api` proxy        |
| `npm run build`        | `tsc --noEmit` then `vite build`         |
| `npm run preview`      | Serve the production build locally       |
| `npm run lint`         | ESLint (flat config, type-checked rules) |
| `npm run typecheck`    | `tsc --noEmit` under strict flags        |
| `npm run test`         | Vitest run (jsdom + Testing Library)     |
| `npm run format`       | Prettier write over `src/`               |
| `npm run format:check` | Prettier check (CI gate)                 |

## Layout

```
src/
  components/        shared UI (AppShell, PlaceholderPage)
  features/          feature areas; MUST NOT import each other (FE-008)
    today/           the Today view (US-4.1 dashboard)
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

The UI is themeable by **swapping token values only**. Four themes ship today,
all derived from the candidate designs in `docs/design/themes/`:

- **Roman** (`docs/design/themes/theme-06-roman.html`) - the **default** light
  theme (decision D-008). Travertine page + faint plaster wash, Pompeiian red
  (`#9e3b2e`) / olive / ochre accents, basalt ink, refined 1px hairline rules, a
  Greek-key meander divider, Cinzel inscriptional caps (display + labels), EB
  Garamond body, Cormorant Garamond italic for accents and ledgers. Functional
  text is **plain English**; Latin is reserved for the wordmark (`VIRID·ARIVM`)
  and decorative motifs only.
- **Dark** (`[data-theme="dark"]`) - first-class "lights out in the greenhouse"
  variant. Deep green-black / charcoal surfaces, warm off-white ink, the same
  Pompeiian / olive / ochre accents tuned brighter for dark, restrained glow
  (no harsh light spill). Same Roman type system.
- **Terracotta** (`docs/design/themes/theme-04-terracotta.html`) - selectable.
  Warm clay: cream + dot-grid background, terracotta / sage / mustard accents,
  chocolate ink, chunky 3px borders, hard-offset shadows, sticker-like rounded
  shapes, Baloo 2 display + Atkinson Hyperlegible body.
- **Herbarium** (`docs/design/themes/theme-01-herbarium.html`) - selectable
  "cleaner view". Botanical editorial: paper cream + ruled-paper texture,
  hairline borders, muted moss / rust / gold, soft engraved-plate shadows,
  squared corners, Fraunces display + Spectral body + IBM Plex Mono labels.

A theme is applied by setting `data-theme` on `<html>`; the token VALUES are
overridden per theme in **one file** - `src/styles/tokens.css` - with no change
to component markup or the Tailwind config.

Every theme's text meets **WCAG AA** (4.5:1 normal, 3:1 large display). The
`src/lib/theme/contrast.test.ts` unit test parses `tokens.css` and asserts the
ratios for ink, muted ink, and the `*-strong` accent tones on each theme's
surfaces, so a contrast regression fails the gate.

### How it works

1. `src/styles/tokens.css` defines every literal value as a semantic CSS custom
   property. `:root` and `[data-theme="roman"]` carry the **default** (Roman)
   values; `[data-theme="dark"]`, `[data-theme="terracotta"]`, and
   `[data-theme="herbarium"]` re-bind the same token NAMES to their values.
2. `tailwind.config.ts` maps each token onto a Tailwind utility via
   `var(--token, fallback)` - e.g. `--color-surface` becomes the `bg-surface`
   / `text-surface` utilities.
3. Components only ever use the utilities (`bg-surface`, `text-accent`,
   `rounded-card`, `font-display`, `font-label`, `shadow-card`, `border-card`,
   `min-h-tap-min`). No raw hex, px, or font names appear in components
   (FE-002).
4. The active theme is chosen at runtime by the **theme controller**
   (`src/lib/theme/`): an inline script in `index.html` resolves the theme
   before first paint (no flash) and sets `data-theme`. Resolution precedence
   (D-008): a valid stored `localStorage["viridarium.theme"]` choice always
   wins; otherwise the OS `prefers-color-scheme: dark` selects `dark`;
   otherwise the Roman default. `getInitialTheme()` in `themeController.ts`
   mirrors this precedence for the typed `useTheme()` hook. The `ThemeToggle`
   control (a native `<select>`) in the app-shell header lets the user switch
   among all four themes and stays reachable on mobile.

### Token catalogue

| Token                     | Tailwind utilities               | Meaning                                    |
| ------------------------- | -------------------------------- | ------------------------------------------ |
| `--color-surface`         | `bg-surface`, `text-surface`     | Default page / card background             |
| `--color-surface-raised`  | `bg-surface-raised`              | Raised surface (header, cards)             |
| `--color-surface-sunken`  | `bg-surface-sunken`              | Recessed surface (wells, inset areas)      |
| `--color-ink`             | `text-ink`                       | Primary text                               |
| `--color-ink-muted`       | `text-ink-muted`                 | Secondary / muted text                     |
| `--color-ink-inverse`     | `text-ink-inverse`               | Text on dark / accent fills                |
| `--color-accent`          | `bg-accent`, `text-accent`       | Brand / primary interactive                |
| `--color-accent-strong`   | `text-accent-strong`             | Stronger accent (hover, headings)          |
| `--color-accent-soft`     | `bg-accent-soft`                 | Tinted accent background (active nav)      |
| `--color-accent-2`        | `bg-accent-2`, `text-accent-2`   | Secondary accent (sage / moss)             |
| `--color-accent-2-strong` | `text-accent-2-strong`           | Stronger secondary accent (hover)          |
| `--color-accent-3`        | `bg-accent-3`, `text-accent-3`   | Tertiary accent fill (ochre / mustard)     |
| `--color-accent-3-strong` | `text-accent-3-strong`           | Tertiary accent as small text (AA-safe)    |
| `--color-danger`          | `text-danger`, `bg-danger`       | Destructive / error state                  |
| `--color-warning`         | `text-warning`                   | Caution state (e.g. overdue soon)          |
| `--color-success`         | `text-success`                   | Healthy / done state                       |
| `--color-border`          | `border-border`                  | Hairlines, dividers, control borders       |
| `--color-ring`            | `ring-ring`                      | Focus ring                                 |
| `--color-overlay`         | `bg-overlay`                     | Scrim behind overlays / menus              |
| `--font-display`          | `font-display`                   | Headings / brand                           |
| `--font-body`             | `font-body`                      | Body copy                                  |
| `--font-label`            | `font-label`                     | Uppercase / tracked micro-labels           |
| `--font-mono`             | `font-mono`                      | Code / IDs / timestamps                    |
| `--radius-card`           | `rounded-card`                   | Card corner radius                         |
| `--radius-control`        | `rounded-control`                | Buttons, inputs, nav items                 |
| `--radius-pill`           | `rounded-pill`                   | Pills / badges                             |
| `--border-width-card`     | `border-card`                    | Card / structural border weight            |
| `--border-width-control`  | `border-control`                 | Control / nav border weight                |
| `--shadow-card`           | `shadow-card`                    | Resting card elevation                     |
| `--shadow-raised`         | `shadow-raised`                  | Raised / floating elevation                |
| `--bg-texture`            | (body `background-image`)        | Decorative page texture (dots / rules)     |
| `--bg-texture-size`       | (body `background-size`)         | Tile size for the texture                  |
| `--motif-meander`         | (`.meander-rule` divider)        | Greek-key meander motif (`none` if unused) |
| `--size-tap-min`          | `min-h-tap-min`, `min-w-tap-min` | 44px minimum tap target (FE-011)           |

`--bg-texture` / `--bg-texture-size` (body texture) and `--motif-meander` (the
`.meander-rule` Greek-key divider) are consumed directly in the `index.css`
base / components layer - a multi-stop `background-image` or repeating motif
does not map to a single Tailwind utility - not via a generated class.

### Adding a token

A **new** token name (new color, new shadow primitive used 3+ times, new
typeface, new structural archetype) is a **design decision** and requires an
ADR (FE-010), not developer discretion. New _combinations_ of existing tokens
are normal dev work.

### Adding a theme (recipe)

Re-binding existing token NAMES to a new palette is normal dev work (no ADR);
adding a brand-new token NAME is a design decision (FE-010). To add a theme:

1. **tokens.css** - add a `[data-theme="<name>"]` block that overrides every
   token the other themes set (copy a block, swap values). Set `--bg-texture`
   and `--motif-meander` to `none` if the theme has no texture / motif. Do not
   introduce new token names.
2. **themeController.ts** (`src/lib/theme/`) - add `"<name>"` to the `THEMES`
   tuple and a label to `THEME_LABELS`. `Theme`, the guard, the cycle, the
   default (`THEMES[0]`-derived), and `getInitialTheme()` all derive from these,
   so nothing else in the controller changes.
3. **index.html** - add `"<name>"` to the inline pre-paint script's `THEMES`
   array (keep it in sync with the controller, or the first paint can flash).
   The script's resolution precedence (stored choice -> prefers-color-scheme
   dark -> Roman default) is fixed; you only extend the valid set.
4. **fonts** - if the theme needs new typefaces, add them to the Google Fonts
   `<link>` in `index.html` (and to the self-hosting follow-up).
5. **contrast** - add the theme's selector to `src/lib/theme/contrast.test.ts`
   `THEME_SELECTORS` so its ink / muted / accent ratios are AA-asserted.
6. The `ThemeToggle` control and `useTheme()` hook pick up the new theme
   automatically from `THEMES`; no component markup changes.

No change to `tailwind.config.ts` or any component is needed - the contract
(token names + Tailwind mapping) is stable.
