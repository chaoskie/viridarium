# Proposal - theme-roman-dark-responsive

Implements decision **D-008** (Roman primary, English labels, first-class dark
theme, mobile/tablet-first, AA contrast). Three filed stories are coupled here
because they share the token system and the app shell.

## Problem

- Terracotta reads as playful and does not match the "Viridarium" name (D-006
  mismatch, see D-008).
- The Roman mockup (`docs/design/themes/theme-06-roman.html`) fixes the feel but
  ships usability hazards: Latin functional labels, low-contrast muted ink and
  italic epigraph, no dark variant, and a desktop-first grid.

## Goals

1. Roman theme becomes the **primary/default light** theme (`:root`). Cinzel
   caps, EB Garamond body, Cormorant Garamond italic accents, Greek-key meander
   divider, Pompeiian red + olive + ochre on travertine, hairline rules.
2. All **functional text is English**; Latin only in the wordmark + one optional
   decorative tagline.
3. First-class **dark theme** (warm greenhouse-at-night). On first load with no
   stored preference, honor `prefers-color-scheme: dark`; stored choice wins.
4. **Mobile + tablet first** shell + Today page: bottom nav on phone, >=44px
   taps, cards stack, theme toggle reachable on mobile.
5. Every theme meets **WCAG AA** for text (4.5:1 normal, 3:1 large).

## Non-goals

- A "Latin labels" fun-toggle (D-008 marks it optional/future, off by default).
- Self-hosting fonts (tracked as a follow-up; still Google Fonts + preconnect).
- Any plant features; this stays the walking skeleton.

## Constraints

- Components stay token-pure (FE-002): no raw hex/px/font literals.
- No new token NAMES without ADR (FE-010). This change only re-binds existing
  names and adds new `[data-theme]` blocks - normal dev work per the README
  recipe. (Exception below.)
- Keep all existing tests green; add the D-008 coverage.

## Comply-or-explain deviations

- **New token names added** (`--color-accent-3-strong`, `--motif-meander`,
  `--color-overlay`): the Roman look needs a darker ochre for AA text, a
  shared meander motif so the divider stays token-pure, and a scrim for the
  mobile menu. These are design-primitive additions (FE-010). Recorded here as
  the written justification; folded into the token catalogue. No second UI
  framework, no component archetype churn.
- **FE-015 a11y space**: axe-core is not yet wired into the Playwright harness
  in this skeleton. Contrast is asserted two ways instead: a Vitest unit test
  computes WCAG ratios over the token sets, and manual ratios are recorded in
  the worklog. Full axe-in-Playwright remains the standing FE-015 follow-up.
