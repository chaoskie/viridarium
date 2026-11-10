# D-006, D-008, D-011: Themes

Three decisions, each refining the one before. The current state is D-011 plus the
guardrails of D-008. Mockups live in [`../design/themes/`](../design/themes/).

## D-006: Terracotta primary, Herbarium secondary (2026-06-07, superseded)

From a five-mockup comparison, Terracotta (warm clay, rounded, playful) was picked as the
default and Herbarium (botanical editorial, cream and serif) as a second built-in theme.

What still stands:

- Themes are token sets over one theme-token contract, switched via a `data-theme`
  attribute, with a user-facing control in Settings.
- Every component stays token-pure (no raw colors), enforced by the frontend rules.
- Shipping more than one theme from day one proves the token layer works.

Superseded: Terracotta as the default (see D-008, then D-011).

## D-008: Roman direction and usability guardrails (2026-06-07)

Terracotta did not fit the name. A Roman theme (inscriptional capitals, a serif body
face, Greek-key meander, Pompeiian red and olive on travertine) replaced it as the
primary light theme. Terracotta and Herbarium stay selectable. Five guardrails keep the
refinement from costing usability:

1. **Functional text is English; Latin is flavor only.** The mockup's Latin labels hurt
   comprehension. Latin stays in the wordmark, an optional tagline and decorative motifs.
   Navigation, room names, statuses and buttons are plain English.
2. **A dark theme is required**, as a first-class variant.
3. **Contrast:** all themes meet WCAG AA for text. This is part of the frontend a11y gate.
4. **Phone and tablet first.** Watering happens away from the desk, so the dashboard must
   work one-handed on a phone. Responsive behavior is a tested requirement.
5. Roman is the primary light theme (superseded by D-011; guardrails 1 to 4 stand).

## D-011: Theme model v2, Viridian default (2026-06-11)

Decided after trying all five themes in the running app.

1. **Light/dark is orthogonal to theme choice.** A mode toggle applies to whichever theme
   is active; "Dark" is no longer a standalone theme.
2. The former Dark theme is Roman's dark variant and plugs in under the toggle.
3. **Viridian is the default theme**, because it tested as the most readable. It gets its
   own dark variant, since a default needs both modes.
4. Dark variants for Herbarium and Terracotta may follow; a missing variant falls back to
   light.
5. Roman stays selectable.

Implementation notes:

- The stored value becomes `(theme, mode)`. A legacy stored `"dark"` migrates to
  `(roman, dark)`.
- `prefers-color-scheme` seeds the default mode and no longer selects a theme.
- `theme-init.js`, the no-JS `:root` default block and the contrast guard (per theme and
  mode) all change with this.

Why: readability won over identity, and splitting theme from mode gives every aesthetic a
usable night mode. Scheduling is tracked in the [roadmap](../roadmap.md).
