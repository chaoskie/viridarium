# Proposal - theme-viridian-candidate (experiment, PO-requested)

Status: in progress. PO asked 2026-06-11 for a candidate "better suiting" UI theme to evaluate ("feel free to experiment"). Tracked on the board; the lock-in decision (default or not, keep or drop) is the PO's, per the D-006/D-008 precedent.

## Idea

**Viridian** - the pigment the app is named after. A Victorian glasshouse / conservatory
read: pale glass-green surfaces, deep pine ink, viridian-green brand accent, fern and
brass secondaries, a faint glass-pane grid texture with sunlight wash. Visually distinct
from all four shipped themes (Roman stone, night greenhouse, clay stickers, herbarium
paper): it is the first *green-led, modern-sans* theme, which arguably suits a plant
app best.

Typography reuses already-shipped self-hosted families (zero new deps, CSP-safe):
Fraunces (display), **Atkinson Hyperlegible (body - the most readable family we ship;
usability over flourish)**, IBM Plex Mono (specimen-tag labels).

## Scope (additive only, PRIN-IX)

- New `[data-theme="viridian"]` token block (re-binds existing token names only - the
  sanctioned recipe; no new token names, no FE-010 ADR needed).
- `viridian` registered in THEMES/THEME_LABELS, theme-init.js, ThemeToggle (automatic),
  contrast guard, entry-html mirror test.
- Default theme **unchanged** (Roman); precedence logic untouched.

## Acceptance

- AC1: all viridian token pairs clear the WCAG AA contrast guard (computed up front:
  every asserted pair >= 5.4:1, lowest margin inverse-on-accent 5.73:1).
- AC2: theme selectable from the toggle, persists, applies pre-paint.
- AC3: existing themes pixel-identical (token blocks untouched); all suites green.
- AC4: production screenshots delivered to the PO for the lock-in decision.

## DoR: PASS (PO-requested experiment; additive token block via the documented recipe; test-first via the contrast guard + theme-set tests).
