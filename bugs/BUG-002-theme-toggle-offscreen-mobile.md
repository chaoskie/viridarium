---
title: Theme dropdown falls off-screen on mobile
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
On the Galaxy S25+ the theme selector in the header is pushed off the right edge of
the screen and cannot be reached.

### Expected behavior
The theme `<select>` is fully within the viewport and reachable on every breakpoint
(FE-011: theme toggle "stays reachable on every breakpoint").

### Steps to reproduce
1. Open the app at phone width (~384 CSS px).
2. Look for the theme selector in the header - it is clipped past the right edge.

### Root cause
**Suspected** (static-read). Almost certainly the same horizontal-overflow cause as
`BUG-001`: the header row (`AppShell.tsx:32`, `flex justify-between`, no wrap) is
wider than the viewport, so the right-aligned phone ThemeToggle (`AppShell.tsx:74`,
`sm:hidden`) sits past the right edge. Confirm during the e2e repro by asserting the
select's bounding box against the viewport.

### Fix sketch
Resolved by the same change as `BUG-001` (stop the header overflowing). If repro
shows an independent cause, fix here: ensure the phone toggle is inside the flow and
within the viewport (the select already uses `min-h-tap-min`; the issue is
horizontal placement, not height).

### Acceptance criteria
- [ ] A Playwright spec at S25+ reproduces the off-screen toggle (red) and now
      passes: the theme `<select>`'s bounding box is fully within the viewport.
- [ ] The toggle is operable (a theme change applies) at phone width.

### Dedupe check
Sibling of `BUG-001-mobile-header-horizontal-overflow` (shared suspected root
cause). Cross-referenced rather than duplicated; one fix likely closes both.

### Context
- **Environment:** local (soak)
- **DB engine:** n/a
- **Version/commit:** f041608
- **Surface:** app shell header
- **Browser/OS:** Samsung Internet / Chrome, Android (Galaxy S25+)

### Notes
See `BUG-001`.
