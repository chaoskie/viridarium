# Proposal - dual-themes

Status: applied. Epic E1 (Foundation) follow-on; the FE-001 design-system lock.

## Problem / why

`scaffold-frontend` shipped a neutral placeholder token set and explicitly
deferred the visual theme (FE-001 lock pending). The product owner has now
chosen two of the five candidate mockups in `docs/design/themes/`:

- **Terracotta** (`theme-04-terracotta.html`) - the DEFAULT.
- **Herbarium** (`theme-01-herbarium.html`) - a secondary "cleaner view".

We need to land both as real, swappable themes on the existing token contract,
with runtime switching, and make the shell genuinely carry each theme's
character (not just recolour).

## Scope (exact, PRIN-IV)

In:

- Extend `tokens.css` to a multi-theme model: `:root` + `[data-theme="terracotta"]`
  carry the default (Terracotta) values; `[data-theme="herbarium"]` re-binds the
  same token names. New token NAMES the two themes need that the neutral set
  lacked: `--color-accent-2/-2-strong/-3`, `--font-label`,
  `--border-width-card/-control`, `--bg-texture`/`--bg-texture-size`. Shadow
  tokens repurposed to hard-offset (Terracotta) vs soft (Herbarium).
- Map the new tokens in `tailwind.config.ts` (`accent-2`, `accent-3`,
  `font-label`, `border-card`, `border-control`).
- Google Fonts for both themes via `index.html` with preconnect
  (Baloo 2, Atkinson Hyperlegible, Fraunces, Spectral, IBM Plex Mono).
- Theme controller (`src/lib/theme/`): pre-paint inline script in `index.html`
  reading `localStorage["plant-care.theme"]`; typed `useTheme()` hook; a
  `ThemeToggle` segmented control in the app-shell header (Settings-page
  placeholder). Default `terracotta`.
- Restyle the shell + Today placeholder + PlaceholderPage to be token-pure and
  read correctly under both themes.
- Unit tests for the controller + hook (default, persistence, switching);
  existing tests kept green.
- Committed design-review screenshots of both themes (FE-012).

Out:

- Self-hosting the fonts (fontsource) - follow-up (offline-first).
- Any plant / room / journal feature (E2-E4); pages stay placeholders.
- axe a11y + perf-budget Audit Spaces (FE-015) - the shell still has no real
  feature surface; deferred to feature stories as in `scaffold-frontend`.
- A third theme; the other three mockups are not implemented.

## Design-system note (FE-010)

New token NAMES are a design decision. They are introduced here as part of the
FE-001 theme lock (the chosen mockups require multi-accent, a label typeface,
explicit border weights, and background textures). This proposal records that
decision; the recipe for further themes is in `frontend/README.md`.

## Deviations (comply-or-explain, PRIN-X)

- **FE-015 (a11y + perf-budget Audit Spaces)** deferred, consistent with
  `scaffold-frontend`. Tap targets (FE-011) are honoured in the new controls
  (`min-h-tap-min`), and all interactive elements have accessible names.
