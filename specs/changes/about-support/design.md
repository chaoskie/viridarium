# Design - `about-support`

## Surfaces

### Footer (app-wide, in `AppShell`)
A slim footer below the routed content, on every page. Content:
`Viridarium · AGPL-3.0 · About · Support`
- "About" → internal `NavLink` to `/about`.
- "Support" → external `<a href={SUPPORT_URL}>` (`target="_blank"`,
  `rel="noopener noreferrer"`), accessible name makes the new-tab + third-party
  nature clear.
- Reuses existing theme tokens / type classes (FE-010, no new primitive).

### `/about` page (new route in `App.tsx`)
A simple page (no new data layer beyond `/health`). Sections (copy APPROVED by
the maintainer 2026-06-18 with edits: privacy line rephrased, README personal
note excerpt added, thank-you added):

- **About Viridarium** - description:
  > Viridarium is an open-source, self-hosted plant-care app - your plant
  > inventory, watering and feeding schedules, and an open API for
  > home-automation, all running on hardware you control.
- **From the maintainer** - a verbatim excerpt of the README "A note from the
  maintainer", with a link to the full note:
  > I built this because the apps already out there didn't quite meet my
  > expectations, and I wanted to make something nice of my own. I own a lot of
  > plants, and some of them are wonderfully picky about water and moisture. Even
  > though it wasn't typed out by my own hands, I am very much the mind behind
  > it: the functionality, the feel, the decisions.

  [Read the full note in the README →](https://github.com/chaoskie/viridarium#a-note-from-the-maintainer)
- **Support** -
  > If Viridarium helps keep your plants alive, you can support its development:
  [linktr.ee/chaoskie](https://linktr.ee/chaoskie) *(opens a third-party site)*
- **Source & license** - Open source under the GNU AGPL-3.0 →
  [github.com/chaoskie/viridarium](https://github.com/chaoskie/viridarium)
- **Privacy** (rephrased per maintainer - the opt-in update check IS an outbound
  call) -
  > Viridarium collects no analytics and makes no outbound connections without
  > your explicit approval. Your data stays on your server.
- **Thanks** -
  > Thanks for using Viridarium - I hope you enjoy it. — chaoskie
- **Version** - read live via `fetchHealth()`; shows `Version X.Y.Z`, or a
  graceful "version unavailable" if `/health` errors (no crash).

## Constants

```
const SUPPORT_URL = "https://linktr.ee/chaoskie";
const REPO_URL = "https://github.com/chaoskie/viridarium";
```

## Version source

Reuse the existing `fetchHealth()` (`GET /api/v1/health` → `{status, version}`).
The About page fetches on mount with the established load/error pattern; a failed
health fetch degrades to "version unavailable" (FE-011, no crash).

## A11y / security

- External links: `rel="noopener noreferrer"`, `target="_blank"`, accessible
  names that say "opens in a new tab" / third-party.
- No app-initiated outbound calls (PRIN-II / SEC-001); the only network call is
  the existing same-origin `/health`. The linktr.ee link is user-initiated
  navigation away from the app.

## Notes for #74a (future, not in this change)

The `/about` page is the intended home for the "Check for updates" button and the
update opt-in/out control. This change leaves a clear section boundary for it but
adds nothing update-related.
