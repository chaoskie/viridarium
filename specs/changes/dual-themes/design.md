# Design - dual-themes

## Multi-theme token model

The two-layer indirection from `scaffold-frontend` is unchanged
(component utility -> Tailwind `var(--token, fallback)` -> tokens.css value).
What changes is that tokens.css now carries **per-theme value blocks** keyed by
`data-theme`, instead of a single `:root`:

```
:root, [data-theme="terracotta"]   -> DEFAULT (Terracotta) values
[data-theme="herbarium"]           -> Herbarium re-binds the SAME names
```

`:root` doubling as terracotta means the no-JS / pre-hydration paint is the
correct default, not a neutral fallback. The Tailwind config and all component
markup are untouched by theme choice - only values move.

### Token additions (FE-010 design decision)

The chosen mockups need primitives the neutral set lacked:

| Token | Why |
| --- | --- |
| `--color-accent-2`, `--color-accent-2-strong` | Both themes have a real second accent (sage / moss) used on actions + brand. |
| `--color-accent-3` | Tertiary accent for feed/snack + gold rules (mustard / gold). |
| `--font-label` | Terracotta labels are Baloo 2 caps; Herbarium labels are IBM Plex Mono tracked caps. Distinct from display + body. |
| `--border-width-card`, `--border-width-control` | The single biggest theme tell: Terracotta 3px chunky vs Herbarium 1px hairline. Must be tokenised, not literal. |
| `--bg-texture`, `--bg-texture-size` | Terracotta dot grid vs Herbarium ruled paper; carried on `body` in the base layer. |

Repurposed (same name, new value): `--shadow-card` / `--shadow-raised` become a
hard offset (`5px 5px 0`) in Terracotta and a low soft offset in Herbarium;
radii go chunky (22px) vs crisp (3px); pills go round vs squared.

## Theme controller

`src/lib/theme/` (shared lib, not a feature - usable everywhere, FE-008 ok):

- **themeController.ts** - the single source of truth: `THEMES` tuple,
  `Theme` type derived from it, `DEFAULT_THEME`, `THEME_STORAGE_KEY`,
  `THEME_LABELS`, plus pure helpers `isTheme`, `readStoredTheme`,
  `applyTheme`, `persistTheme`, `nextTheme`. All storage access is wrapped in
  try/catch so private-mode / disabled storage never throws.
- **useTheme.ts** - typed hook: initialises state from `readStoredTheme()`
  (matching the inline script), re-applies on mount via `useEffect`, and
  exposes `setTheme` + `cycleTheme` that apply + persist together.
- **index.html inline script** - mirrors KEY / THEMES / DEFAULT and sets
  `data-theme` before the bundle loads, so there is no flash of the default
  theme when Herbarium is the stored choice. The README records the
  keep-in-sync constraint.

`ThemeToggle` (a shared component) renders a segmented control of all
`THEMES`; each option is a real button with an accessible name and a
`min-h-tap-min` target, `aria-pressed` reflecting the active theme.

## Restyle approach

Components stay token-pure: the shell, Today hero/stat-pods, HealthBadge and
PlaceholderPage use `border-card`/`border-control`, `shadow-card`/`shadow-raised`,
`rounded-*`, `font-display`/`font-label`, and the accent scale. Because every
visual literal is a token, the same markup reads as sticker-chunky under
Terracotta and engraved-editorial under Herbarium with zero conditional CSS.

## Verification

`vite build` then `vite preview`, screenshot both themes at 1280-wide via the
Playwright MCP browser, saved to `docs/design/themes/implemented-*.png`
(FE-012). (The sandboxed dev server cannot write `node_modules/.vite`, so
preview-of-build is used instead of `npm run dev`.)
