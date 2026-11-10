# Research: installable mobile app (2026-07-06)

Status: research, not ratified. Entering a release phase needs a product-spec amendment
(`SPEC-001`).

## Verdict

**PWA first.** It needs no backend changes (the static mount already serves anything
Vite emits, the CSP is compatible, the API client uses same-origin relative URLs), has no
app-store gatekeeping and costs a solo maintainer almost nothing to keep up. Capacitor
only becomes interesting if offline local notifications become a hard requirement. Tauri
mobile and React Native are overkill.

## Why not Capacitor for now

- Pointing `server.url` at a remote instance is officially dev-only. The production
  pattern is to bundle the build, make the API base a configurable absolute URL and add
  `capacitor://localhost` to CORS.
- Distribution burden: paid developer accounts for both stores, developer verification
  that adds friction even to sideloading, and pipeline work for F-Droid.
- The only real gains are local notifications (reminders without a push server or HTTPS)
  and camera integration.

## Implementation path

1. `vite-plugin-pwa` with the `generateSW` strategy: manifest (name, standalone, 192 and
   512 px plus maskable icons), `navigateFallback: /index.html` with `/api/` on the
   denylist, NetworkFirst runtime caching for GET `/api/v1/*`.
2. Icons, `apple-touch-icon` and a `theme-color` meta tag in `frontend/public/` and
   `index.html`. Reconcile `theme-color` with the multi-theme system in `theme-init.js`.
3. Verify that the built `dist/` serves the manifest and `sw.js` through the backend
   static mount under the strict CSP (Lighthouse audit against the Docker image).
4. Update-available toast via `virtual:pwa-register`.
5. Documentation, "Install on your phone": **HTTPS is a hard prerequisite.** Service
   workers need a secure context, and a plain `http://` LAN address does not qualify.
   Recommend a reverse proxy with a real certificate, or a VPN that provides HTTPS. On
   iOS, installation is manual (Share, then Add to Home Screen), and Web Push needs iOS
   16.4 or later and an installed PWA.
6. Optional later: Web Push reminders with VAPID and a device-scoped
   `push_subscriptions` table. This needs no login, so it fits
   [D-003](../decisions/D-003-no-auth-trust-boundary.md). Messages still transit Apple
   and Google push infrastructure, so it must be opt-in, in the spirit of
   [D-015](../decisions/D-015-update-check-and-self-update.md).

Effort: about one to two days of app work. The HTTPS story is deployment documentation,
not code.
