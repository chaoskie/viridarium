# Proposal - csp-prod-fonts-theme (bugfix, v0.1 release gate)

Status: in progress. Found during US-2.2 production-path verification; tracked as VIRIDARIUM-37 (high). Blocks any "v0.1 usable" claim.

## Problem

When the backend serves the built SPA (the production single-container path), the
SEC-011 CSP (`script-src 'self'; style-src 'self'`) blocks two things `index.html`
depends on, with a console error each on every page:

1. the Google Fonts stylesheet (`style-src` violation) - all four themes fall back to
   system fonts in production;
2. the inline theme pre-paint script (`script-src` violation) - the persisted theme is
   not applied before first paint (flash / apparent non-persistence).

Invisible in Vite dev (no CSP there). The CSP itself is correct; the entry HTML is what
must comply.

## Fix (exact scope, PRIN-IX)

- **Self-host the fonts via @fontsource** (static packages, exact same family names, the
  weights/styles the Google css2 URL loaded): Cinzel, EB Garamond, Cormorant Garamond,
  Baloo 2, Atkinson Hyperlegible, Fraunces, Spectral, IBM Plex Mono. Imported from a
  single `src/styles/fonts.ts`, bundled by Vite, served same-origin. Removes the last
  external runtime dependency (also satisfies the offline-first NFR, product-spec §7).
  Known trade-off: static Fraunces drops the `opsz` variable axis the Google URL had;
  visual delta is minor and acceptable (usability over flourish).
- **Externalize the theme pre-paint script** to `public/theme-init.js` (copied to the
  dist root by Vite, served same-origin, still a blocking script in `<head>` so it runs
  before paint). Content unchanged; KEY/THEMES/DEFAULT stay mirrored with
  `themeController.ts`.
- **CSP unchanged**: with nothing external left, the strict policy simply passes.

## Out of scope

No CSP relaxation, no nonce/hash plumbing, no e2e harness (TEST-010 enforcement lands
with the Playwright suite), no font subsetting.

## Acceptance

- AC1: built SPA served by the backend produces zero console errors (production-path
  smoke, real browser).
- AC2: a stored theme is applied before first paint on a cold load; all four themes
  render their locked fonts (FE-001) in production.
- AC3: `index.html` references no external origin and contains no inline script
  (regression-pinned by test).

## DoR: PASS (release-gate bug; contained to entry HTML + font loading; test-first via the entry-HTML contract test + production-path smoke).
