# Design - theme-roman-dark-responsive

## Token system

Four `[data-theme]` blocks in `src/styles/tokens.css`:

- `:root, [data-theme="roman"]` - DEFAULT. Travertine `#efe7d6` surface,
  plaster `#f6f0e3` raised, basalt `#2a2620` ink, Pompeiian red `#9e3b2e`
  accent, olive `#5b6a42` accent-2, ochre/gold accent-3. Hairline rules
  (`#a89a78`). Cinzel display + label, EB Garamond body, Cormorant Garamond as
  an italic accent (mapped to `--font-accent`... no - kept on `font-display`
  italics via component classes; we reuse existing names only where possible).
- `[data-theme="dark"]` - greenhouse at night. Deep green-black surface
  `#161a14`, charcoal raised `#1f241c`, warm off-white ink `#ece7da`, accents
  tuned brighter for dark (Pompeii `#d76a57`, olive `#9cb277`, ochre `#d6a94e`).
- `[data-theme="terracotta"]` and `[data-theme="herbarium"]` - unchanged values,
  retained as selectable.

### Contrast fixes (vs mockup)

- `--color-ink-muted` darkened from the mockup's `#6b6354` (3.9:1 on travertine,
  fails) to `#5c5444` (>=4.6:1).
- The italic epigraph uses `--color-ink-muted` (not the mockup's lighter soft
  ink) so it clears 4.5:1.
- Accent-3 text on travertine uses a darker ochre `--color-accent-3-strong`
  (`#7a5a18`) for AA; the lighter `#b58a32` is fill-only.

### New token names (FE-010, justified in proposal)

- `--color-accent-3-strong` -> `text-accent-3-strong`.
- `--motif-meander` -> consumed by the `.meander-rule` component class in
  index.css (a repeating Greek-key SVG, per theme).
- `--color-overlay` -> the mobile-menu scrim (only the dark/light value differs).

## Shell responsiveness

- **Phone (< sm, 390px)**: header shows wordmark + theme toggle only; primary
  nav becomes a fixed **bottom bar** (`<nav>` with `min-h-tap-min` items,
  icon+label). Main content gets bottom padding so the bar never covers content.
- **Tablet (sm..lg, 820px)**: header wordmark + inline nav wraps; toggle inline.
  Bottom bar hidden.
- **Desktop (lg+, 1280px)**: same as tablet, wider max width, meander divider
  under header.
- Cards stack single-column on phone, 2-up tablet, auto-fill on desktop
  (`grid` with responsive `grid-cols`).

## Theme toggle UX

A compact **select** (`<select>` styled as a control) in the header, labeled
"Theme", listing Roman / Herbarium / Terracotta / Dark. Chosen over the
segmented 4-button control because four buttons crowd a 390px header; a native
select is one tap, fully keyboard/AT accessible, and 44px tall. The toggle
sits in the header on every breakpoint (always reachable on mobile).

## Pre-paint default + prefers-color-scheme

`index.html` inline script:

1. Read `localStorage["viridarium.theme"]`; if valid, use it.
2. Else if `window.matchMedia("(prefers-color-scheme: dark)").matches`, use
   `"dark"`.
3. Else use `"roman"`.

`themeController.ts` mirrors this with `resolveInitialTheme()`:
`readStoredTheme()` returns `null` when nothing valid is stored; a new
`systemPrefersDark()` + `getInitialTheme()` apply the same precedence. `useTheme`
initialises from `getInitialTheme()`. A stored value always wins after.

## Tests added

- `themeController`: `getInitialTheme()` returns `dark` when no stored value and
  system prefers dark; returns `roman` otherwise; stored value overrides system.
- `useTheme`: initialises dark by prefers-color-scheme; persistence across the
  full set (roman <-> dark <-> herbarium).
- `contrast.test.ts`: parses tokens.css, computes WCAG ratios for ink and
  muted-ink on each theme's surfaces, asserts >= 4.5 (and accents as large >= 3).
- `App.test`: responsive smoke - bottom nav present, header toggle present,
  English labels only (no HODIE/TRICLINIUM/etc.).
