# Frontend (`FE-*`)

**Enforces:** React/TypeScript frontend consistency - design system, tokens, CSS/TS hygiene, feature isolation - plus the UI test discipline (Playwright POM, locators) and the cross-cutting **Audit Spaces** baselines. Consumed by frontend developers, the code-reviewer, and the test-engineer. Stack per ARCH-001 (React 18+, TypeScript strict, Vite, Tailwind CSS, ESLint + Prettier).

---

## Design system

### FE-001 — Design-system lock
Before any UI code, the following are locked in writing (changes via ADR, ARCH-010):
1. **Component approach:** a small set of in-repo primitive components (button, input, modal, table, card) built on **Tailwind CSS** utilities; no second UI framework added without an ADR.
2. **Design tokens** (FE-002).
3. **Visual reference** (named app or mood board).
*Targets:* design work, frontend developer.

### FE-002 — Central design tokens
Colors, spacing, and typography live as central design tokens (the Tailwind theme config / CSS custom properties). Hardcoded hex colors, arbitrary spacing values, or font values inside components are a **review red flag**; use theme tokens and Tailwind scale classes.
*Targets:* frontend developer, code-reviewer.

### FE-003 — CSS hygiene
Styling is via Tailwind utility classes plus component-scoped CSS where utilities are insufficient. **No `!important`**; no global style leakage. Where custom CSS is needed, class names are **kebab-case and functional** (`.change-indicator`, not `.yellow-dot`). JSX attributes use double quotes. No inline `style` for anything a token/utility can express.
*Targets:* frontend developer, code-reviewer.

### FE-004 — Strict TypeScript
TS strict compiler flags are on. **No `any`, no `object`, no `{}`** as types; `unknown` only as a last resort with narrowing. Applies to all TS in the repo (React app, Playwright tests, tooling). Verified by `tsc --noEmit` (`QG-001`).
*Targets:* frontend developer, code-reviewer, ci.

### FE-005 — React idiom
Function components with hooks only; no class components. Hooks obey the rules of hooks (top-level, stable order). Side effects live in `useEffect`/event handlers, never in render. Prop and state types are explicit. For anything not covered by these rules, follow the React + TypeScript community conventions and the project ESLint config.
*Targets:* frontend developer.

### FE-006 — Prettier + ESLint baseline (pinned)
Prettier is the formatter and ESLint the linter, both with pinned configs committed to the repo. The formatter runs only on touched files ([[00-constitution#PRIN-IX Minimal Changes|PRIN-IX]]). ESLint runs in the mechanical gate (`QG-001`).
*Targets:* frontend developer, ci.

### FE-007 — Bundle budgets
A production bundle-size budget is declared (Vite build size check / `rollup-plugin-visualizer` threshold or a CI size assertion). Tighten per project; never remove. A regression past the budget fails the gate.
*Targets:* ci, frontend developer.

### FE-008 — Feature isolation
Feature areas MUST NOT import from each other (`features/X` cannot import `features/Y`); shared code lives in designated shared dirs. Enforced mechanically (ESLint module-boundary / `no-restricted-imports` rules), part of the QG-001 gate.
*Targets:* frontend developer, code-reviewer, ci.

### FE-009 — Component-reuse red flags
Review red flags: a hand-built `<table>` where the shared table component exists; an inline confirmation where the shared modal exists; shared styles redefined page-locally.
*Targets:* code-reviewer.

### FE-010 — Visual-primitive dispatch trigger
A **new** visual primitive - new color token, new shadow primitive (used 3+ times), new typeface, or new structural component archetype - is a **design decision** (ADR), not developer discretion. New combinations of existing primitives are normal dev work.
*Targets:* frontend developer, design work.

## UI quality baselines

### FE-011 — Accessibility baseline
Every interactive element has an accessible name (`aria-label` or readable text); every form input has an associated `<label>`; tap targets ≥ 44×44 px; no horizontal scroll; mobile-first.
*Targets:* frontend developer, test-engineer.

### FE-012 — Design-review screenshots (committed)
Every UI-touching story closes with rendered screenshots at the locked breakpoints, **committed to the change's folder** as design-review evidence.
> Distinct from TEST-011: *failure-capture* screenshots stay ephemeral and uncommitted; *design-review evidence* screenshots are deliberate, curated artifacts and ARE committed.
*Targets:* frontend developer, reviewer-gate, DoD template.

### FE-015 — Audit Spaces (per-story mandatory baselines)
Two cross-cutting spaces are asserted automatically for **every** UI story; opting out requires written justification in the change's proposal:
- **a11y space** - automated scan (axe-core via Playwright) + FE-011 assertions.
- **perf-budget space** - FE-007 budgets enforced as a test/CI assertion, not just a build warning.
The backend secure-headers / no-PII-in-logs concerns live in `SEC-*` (the security-headers baseline is SEC-011).
*Targets:* test-engineer, ci, DoD template.

## Playwright discipline

### FE-013 — Page Object Model
Acceptance/e2e uses POM: `.po.ts` files contain **only locators**; the app has a `base.po`; reusable elements live in a common base; page subsections become `.co.ts` components.
*Targets:* test-engineer, frontend developer.

### FE-014 — Locator priority
Locator preference order: `getByTestId` → `getByLabel` / `getByPlaceholder` / `getByText` (if unique) → `getByRole` → raw `locator()` as last resort. No chained DOM-walking; no framework-generated class locators.
*Targets:* test-engineer, frontend developer.
