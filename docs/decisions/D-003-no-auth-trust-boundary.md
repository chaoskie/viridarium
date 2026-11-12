# D-003: No authentication, documented trust boundary

Status: ratified, 2026-06-07.

## Decision

v1 ships with no user authentication. The deployment model is a trusted network (LAN or
VPN) or the user's own auth proxy in front of the app. This is stated prominently in
[SECURITY.md](../../SECURITY.md) and the [README](../../README.md).

## Why

The app is single-user by design, and forced accounts are a recurring complaint about
existing self-hosted plant apps. Skipping login is a differentiator, not an omission.

## Consequences

- [`rules/security.md`](../../rules/security.md) is written around a trust boundary and
  secure defaults, not around an identity provider (`SEC-003`).
- Any future authentication would be opt-in and contributed, never mandatory.
- Features that would phone out or widen privilege are held to this posture, see
  [D-015](D-015-update-check-and-self-update.md).
