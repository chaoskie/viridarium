# Tasks - `about-support`

One frontend lane (PRIN-VI). No backend.

## T0 - Gate: maintainer copy approval (BLOCKS apply)
- [ ] Maintainer approves/edits the About-page copy (open question 1). DoR
      item 13 cannot close until this is resolved.

## T1 - Footer + About page (after T0)
- [ ] `AboutPage` component + `/about` route in `App.tsx`.
- [ ] App-wide footer in `AppShell` (About + Support links).
- [ ] `SUPPORT_URL` / `REPO_URL` constants; external links new-tab + rel.
- [ ] Live version via `fetchHealth()` with graceful failure.

## T2 - Tests (TDD, red-before-green)
- [ ] Footer renders on a page; Support link has correct href + target + rel.
- [ ] `/about` renders description, support link, license/source link,
      privacy statement.
- [ ] Version renders from a stubbed `/health`; health failure shows the
      graceful fallback, no crash.

## T3 - Acceptance + evidence
- [ ] Playwright FE-012 screenshots of `/about` + footer (S25+ + desktop).
- [ ] Full FE gate green; review gate; PR.
