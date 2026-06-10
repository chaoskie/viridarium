# Tasks - theme-roman-dark-responsive

- [x] T1  tokens.css: add `:root`/`[data-theme="roman"]` default + `[data-theme="dark"]`; keep terracotta + herbarium; contrast fixes; new tokens.
- [x] T2  tailwind.config.ts: map new tokens (`accent-3-strong`, overlay).
- [x] T3  index.css: meander rule component class + bottom-nav safe-area padding.
- [x] T4  index.html: fonts (Cinzel, EB Garamond, Cormorant Garamond) + pre-paint script with prefers-color-scheme.
- [x] T5  themeController.ts: THEMES set (roman default), labels, getInitialTheme + systemPrefersDark.
- [x] T6  useTheme.ts: initialise from getInitialTheme.
- [x] T7  ThemeToggle.tsx: accessible select control.
- [x] T8  AppShell.tsx: responsive shell, bottom nav, meander divider, English labels, wordmark.
- [x] T9  TodayPage.tsx restyle (English, responsive, token-pure). HealthBadge + PlaceholderPage already English/token-pure.
- [x] T10 Tests: themeController, useTheme, contrast, App responsive/labels smoke (39 pass).
- [x] T11 README: token catalogue + add-a-theme recipe + theme list + default.
- [x] T12 Gates: fe-lint fe-format-check fe-typecheck fe-test fe-build all green.
- [x] T13 Screenshots at 1280/820/390 for roman + dark in /tmp/viridarium-shots/.
