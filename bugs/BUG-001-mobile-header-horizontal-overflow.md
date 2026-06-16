---
title: Page opens zoomed on mobile (horizontal overflow)
tags:
  - bug
  - frontend
  - a11y
status: open
severity: high
evidence: static-read
created: 2026-06-16
related-change: mobile-soak-fixes
work-item: "-"
---

### Observed behavior
On a Samsung Galaxy S25+ the app opens in a "somewhat zoomed" state - content does
not sit at the native 1.0 scale and the layout is wider than the screen.

### Expected behavior
The page renders at the device width with no horizontal scroll and visual-viewport
scale 1.0 (FE-011: "no horizontal scroll; mobile-first").

### Steps to reproduce
1. Open the app on a phone-width viewport (~384 CSS px, the S25+).
2. Observe the page is horizontally scrollable / appears zoomed to fit width.

### Root cause
**Suspected** (static-read). The `<meta name="viewport">` in `frontend/index.html`
is correct (`width=device-width, initial-scale=1.0`), so the cause is an element
forcing the document wider than the layout viewport. Prime suspect: the
non-wrapping header row in `frontend/src/components/AppShell.tsx:32`
(`flex ... justify-between` with no wrap) - the wide-tracked `VIRID·ARIVM` wordmark
(`text-xl tracking-widest`) + 44px glyph on the left and the "THEME" label + select
on the right exceed ~384 px. The fixer MUST confirm the actual overflowing node via
the e2e repro (page-evaluate for `scrollWidth > clientWidth`) before editing;
refuting the header hypothesis is a valid outcome.

### Fix sketch
Eliminate the overflow at its source (do **not** mask with `overflow-x-hidden`).
Likely: let the brand group shrink (`min-w-0` + `truncate` on the wordmark) and
drop the visible "THEME" label on phones (keep it as the select's `aria-label`).
Blast radius: `AppShell.tsx`, possibly `ThemeToggle.tsx`.

### Acceptance criteria
- [ ] A Playwright spec at the S25+ viewport reproduces the overflow (red) and now
      passes: `document.documentElement.scrollWidth <= clientWidth`.
- [ ] Visual-viewport scale is 1.0 on first paint at phone width.
- [ ] No horizontal scrollbar on the Today and Plants pages at S25+.

### Dedupe check
`bugs/` empty before this batch. Shares a root-cause class with
`BUG-005-long-values-break-mobile-layout` (overflow from long content) and is the
sibling of `BUG-002-theme-toggle-offscreen-mobile` (same suspected cause).

### Context
- **Environment:** local (soak)
- **DB engine:** n/a (frontend layout)
- **Version/commit:** f041608
- **Surface:** all pages (app shell)
- **Browser/OS:** Samsung Internet / Chrome, Android (Galaxy S25+)

### Notes
Confirm vs `BUG-002` during repro - if the zoom and the off-screen toggle have
different causes, split the fixes.
