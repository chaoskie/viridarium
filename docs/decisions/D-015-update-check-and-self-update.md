# D-015: Update check and in-app self-update direction

Status: direction decided 2026-06-18, not yet specified or built. Constrained by
[D-003](D-003-no-auth-trust-boundary.md) and the stack-amendment discipline of
[D-010](D-010-add-python-multipart.md).

## Context

The goal is an unobtrusive "update available" signal and, ideally, an in-app upgrade
path for non-technical self-hosters, without weakening the privacy and security posture.

## Decision

### Part A: version check

- **Proxied by the backend**, never browser to GitHub. Clients never call out, so a
  user's IP address is not exposed to a third party; only the server's is.
- **Opt-in.** Until a first-use setup flow exists, a Settings toggle that defaults to
  off.
- **Cadence:** when enabled, at most one automatic check per week, on load. Plus a manual
  "Check for updates" button on the `/about` page.
- **Source of truth:** the latest GitHub Release of `chaoskie/viridarium`, queried
  unauthenticated, compared with the app version from `/api/v1/health`. The app notifies
  and links the release notes. It does not apply anything.
- The `/about` privacy line already covers this: no outbound connections without
  explicit approval.

### Part B: applying an update (design pending)

- **Not** the Docker socket inside the app container. Mounting the socket equals host
  root and contradicts secure-by-default. Rejected as a default.
- **Chosen direction:** an opt-in updater sidecar, set up once by whoever deploys the
  app. Two modes, neither needing technical knowledge from the end user:
  1. automatic weekly background update, or
  2. an in-app "Update now" button that calls the sidecar's token-protected HTTP API to
     pull and recreate.
- The app container stays socket-free. Only the opt-in sidecar holds that privilege, and
  it is explicit and visible.
- This needs its own spec with the security reviewer involved before any build.

Research on sidecar options and image tagging:
[../research/upgrade-path.md](../research/upgrade-path.md).

## Why it matters

Privacy and trust are the point of this app. An update mechanism is where the temptation
to phone home or take socket access is strongest, so the design is deliberately
conservative: proxy the check, default it off, keep the update privilege out of the app.
