# Proposal - `about-support`

**Work item:** VIRIDARIUM-76
**Type:** feature (frontend; reads existing `/health`, no new API)

## Story

As a user (and as the maintainer), I want an About page and an always-present
footer with the project's support/donation link and basic project info, so that
people can learn what Viridarium is, follow/support the maintainer, and find the
source and license - without any of it compromising the privacy posture.

## Scope

In scope:
- A slim, app-wide footer (rendered in `AppShell`) with: project name + license,
  a link to the About page, and a Support link (the maintainer's linktr.ee).
- A dedicated `/about` route/page with: project description, Support link,
  source + license, a privacy statement, and the live app version (from
  `GET /api/v1/health`).
- External links open in a new tab with `rel="noopener noreferrer"` and are
  labelled as leading to a third-party site.

Out of scope (explicit):
- No new backend/API (version reuses the existing `/health` endpoint).
- The "Check for updates" button is **#74a**, not here. The `/about` page is
  designed to host it later; this change does not add it.
- No analytics, no outbound calls from the app itself - the Support/social links
  are plain user-initiated `<a href>` navigations (PRIN-II, SEC-001).

## Open questions (maintainer-facing, scope-affecting)

1. **About-page copy** - the wording is the maintainer's. A draft is in
   `design.md`; the maintainer edits/approves before `/spec-apply`. **(OPEN -
   awaiting maintainer copy approval.)**
2. **Placement** - footer (app-wide) + dedicated `/about` page, no new top-nav
   item. Assumed per the maintainer's "About page (or footer)"; confirm.
3. **Support URL** - `https://linktr.ee/chaoskie` (provided 2026-06-18); it
   aggregates BuyMeACoffee, PayPal.me, Instagram, GitHub.

Items 2-3 are assumed-resolved; item 1 (copy) must be approved before apply.

## OpenAPI delta

None - no REST surface added (`/health` already returns `version`).

## Acceptance criteria

- **AC1** A footer is visible on every page with About + Support links; the
  Support link points to the approved URL, opens in a new tab, `rel="noopener
  noreferrer"`.
- **AC2** `/about` renders the approved project description, Support link, source
  + license (AGPL-3.0) link, and the privacy statement.
- **AC3** `/about` shows the live version from `GET /api/v1/health` (and degrades
  gracefully if health is unavailable - no crash, no perpetual spinner).
- **AC4** No outbound network calls are introduced by the app itself; external
  links are user-initiated navigations only.
- **AC5** FE-012 design-review screenshots (About + footer, S25+ and desktop)
  committed.
