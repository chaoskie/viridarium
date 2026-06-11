# Worklog - csp-prod-fonts-theme

`time · actor · action · artifact · ref` (newest first). Story ids only, no tracker UUIDs.

## Entries

- `~03:35 · orchestrator/Fable · production-path smoke PASS (amendment requirement): built SPA served by backend (port 8431, strict CSP confirmed via header) in a real browser - ZERO console errors/warnings; pre-paint theme applied on cold load (roman default, persisted herbarium + terracotta both honored before paint); per-theme font faces lazily loaded and verified via document.fonts (roman: Cinzel 600/700 + EB Garamond 400/500 + Cormorant 500i; herbarium: Fraunces 600/900 + Spectral 400/500 + Plex Mono 400/500; terracotta: Baloo 2 600/700 + Atkinson 400) · playwright session · SEC-011/TEST-010-precursor`
- `~03:20 · orchestrator/Fable · fix applied: 8 @fontsource packages (weights mirror the old css2 URL; static Fraunces, opsz dropped per proposal) imported via src/styles/fonts.ts; theme pre-paint moved to public/theme-init.js (blocking, same-origin); index.html externals removed; CSP untouched. GREEN: 134 frontend tests, lint/tsc/prettier clean, build OK (css 63 kB, js 208 kB - FE-007 budget) · frontend/ · SEC-011/PRIN-IX`
- `~03:10 · orchestrator/Fable · TEST-014 red recorded: entry-html-csp contract test failed 3/3 (googleapis reference, inline script, no theme-init.js) · frontend/src/entry-html-csp.test.ts · TEST-014`
- `~03:00 · orchestrator/Fable · bugfix opened (v0.1 release gate, found during US-2.2 prod-path verification); branch fix/csp-prod-fonts-theme off main · specs/changes/csp-prod-fonts-theme · SEC-011/REV-003`
