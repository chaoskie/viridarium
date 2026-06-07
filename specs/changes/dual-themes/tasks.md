# Tasks - dual-themes

- [x] T1 Extend `tokens.css`: `:root`+`[data-theme="terracotta"]` default
      (Terracotta) block; `[data-theme="herbarium"]` override block. Add
      `--color-accent-2/-2-strong/-3`, `--font-label`,
      `--border-width-card/-control`, `--bg-texture`/`--bg-texture-size`;
      repurpose shadows/radii per theme.
- [x] T2 Map new tokens in `tailwind.config.ts` (`accent-2`, `accent-2-strong`,
      `accent-3`, `font-label`, `border-card`, `border-control`).
- [x] T3 Apply `--bg-texture`/`--bg-texture-size` on `body` in `index.css`
      base layer.
- [x] T4 Google Fonts for both themes in `index.html` (preconnect + the five
      families).
- [x] T5 Pre-paint inline theme script in `index.html`
      (key `plant-care.theme`, default terracotta).
- [x] T6 Theme controller `src/lib/theme/themeController.ts` (THEMES, type,
      default, storage key, labels, guard, read/apply/persist/next).
- [x] T7 `useTheme()` hook `src/lib/theme/useTheme.ts`.
- [x] T8 `ThemeToggle` segmented control + wire into `AppShell` header.
- [x] T9 Restyle shell + Today (hero + stat pods) + HealthBadge +
      PlaceholderPage to be token-pure under both themes.
- [x] T10 Unit tests: `themeController.test.ts` + `useTheme.test.ts`
      (default, persistence, switching, guard); update `App.test.tsx` heading
      assertion for new Today copy; keep all green.
- [x] T11 Update `frontend/README.md` token catalogue + multi-theme model +
      "add a third theme" recipe.
- [x] T12 Build + preview; screenshot both themes to
      `docs/design/themes/implemented-{terracotta,herbarium}.png` (FE-012).
- [x] T13 Spec artifacts (proposal / design / tasks / worklog).
- [x] T14 Gates green: fe-lint / fe-format-check / fe-typecheck / fe-test /
      fe-build.

## Follow-ups (not this story)

- Self-host the theme fonts via `@fontsource` (Baloo 2, Atkinson Hyperlegible,
  Fraunces, Spectral, IBM Plex Mono) for offline-first; drop the Google Fonts
  `<link>` once bundled.
- FE-015 Audit Spaces (axe a11y scan + perf-budget assertion) on the first real
  feature story.
- A real Settings page; `ThemeToggle` in the header is the interim placeholder.
