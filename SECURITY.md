# Security Policy

## Deployment model (read this first)

This application ships **without user authentication by design**. It targets trusted-network deployment: a home LAN, a VPN (Tailscale/WireGuard), or behind a reverse proxy that adds authentication (Authelia, Caddy basic auth, etc.).

**Do not expose it directly to the public internet.** If you do, anyone can read and modify your data. This is a documented trust boundary, not a vulnerability.

Hardening that IS in scope and enforced:

- No secrets in the repo or the image; configuration via environment variables.
- No personal data in logs or error responses.
- Dependencies scanned for known CVEs in CI.
- Sane security headers and CORS defaults.
- SQL access through parameterized queries only (SQLAlchemy ORM/core).

## Supported versions

Only the latest minor release receives security fixes.

## Reporting a vulnerability

Use [GitHub Private Vulnerability Reporting](../../security/advisories/new) (Security tab, "Report a vulnerability"). Please do not open public issues for security reports.

This is a solo-maintainer project: you will normally get a first response within a week. Coordinated disclosure is appreciated; you will be credited in the advisory and changelog unless you prefer otherwise.
