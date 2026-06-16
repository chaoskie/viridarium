# Worklog - `mobile-soak-fixes`

Per-change trail (`TRACE-001`). Entries **newest-first**, one line each:
`time · actor · action · artifact · ref`. Bug batch from Galaxy S25+ soak
(BUG-001..005), filed via the `/bug` workflow.

## Entries

- `23:05 · claude/OPUS · review fixes applied: vite preview fallback 8000->8799 (comment now true); removed dead acquiredOnLabel POM locator; annotated characterisation tests · vite.config.ts, e2e/plant-form.co.ts, PlantFormModal.test.tsx · REV-003`
- `23:00 · claude/OPUS · REVIEW GATE (three reviewers): security PASS (0 blocking); scope PASS + 1 WATCH; code WATCH. Findings: 2 MEDIUM (fixed: vite comment/code, dead POM locator) + characterisation-test audit-trail (addressed below). No CRITICAL/HIGH code/security/scope blockers · /review · QG-004/REV-003`
- `23:00 · claude/OPUS · WATCH (carry to retro): the 4 PlantFormModal characterisation tests (partial-fill, empty name, whitespace name, maxLength caps) pass against reverted main - they guard PRE-EXISTING behaviour at the user's input-hardening request, not red-first TDD. Comply-or-explain: TEST-014 red requirement intentionally waived for these specific tests; behavioural reds for BUG-001/002/003/005 are recorded; annotated inline in the test file · PlantFormModal.test.tsx · PRIN-X/TEST-014/QG-004`
- `22:50 · claude/OPUS · audit gate finding: make audit RED on 4 starlette 0.49.3 CVEs - PRE-EXISTING on main (version unchanged), backend untouched by this batch; filed BUG-006, escalated to user; NOT fixed here (PRIN-IX, security decision) · bugs/BUG-006 · PRIN-VII/SEC-009`
- `22:48 · claude/OPUS · reverted backend/uv.lock to main (uv sync had only reconciled requires-dist metadata; no version change) - keeps PR backend-clean · backend/uv.lock · PRIN-IX`
- `22:47 · claude/OPUS · DoD partial: backend 459 tests pass 99.6% cov (unaffected); fe lint/format/typecheck green; fe-test 224 pass; e2e 11 pass serially · - · QG-002`
- `22:44 · claude/OPUS · deviation (comply-or-explain): BUG-004 is a cosmetic label/hint; its unit test is a green guard (no recorded red). Behavioural reds for BUG-001/002/003/005 are recorded above; blank-saves behaviour characterised by the partial-fill test · - · PRIN-III/TEST-014`
- `22:42 · claude/OPUS · GREEN: all 5 regression specs pass at S25+ after fixes (header min-w-0+hide phone Theme label; Modal max-h+scroll; acquired-on optional+hint; plant display break-words+min-w-0). FE-012 screenshots committed (phone+desktop) · src/components, src/features/plants, bugs/mobile-soak-screenshots · BUG-001..005`
- `22:38 · claude/OPUS · harness made serial (workers=1) - shared single SQLite backend flaked under parallel workers (db-locked) · playwright.config.ts · TEST-009`
- `22:30 · claude/OPUS · RED captured (TEST-014) at S25+ 384x740: BUG-001 hasHorizontalOverflow=true; BUG-002 theme select right edge 438 > 384; BUG-003 Name field toBeInViewport ratio 0 (clipped, unscrollable); BUG-005 submit click intercepted by overflowing modal. Today-view a11y passed. · e2e/*.spec.ts · PRIN-III/TEST-014`
- `22:24 · claude/OPUS · harness: dedicated acceptance backend port 8799 (never 8000) wired via E2E_BACKEND_PORT - avoids colliding with a dev backend / unrelated local service · playwright.config.ts, vite.config.ts, run-backend.sh · PRIN-IX`
- `22:20 · claude/OPUS · Playwright acceptance layer scaffolded (config, e2e POM, fixtures, Makefile fe-e2e) - implements already-locked ARCH-001/TEST-009; no PRIN-V amendment · frontend/e2e, playwright.config.ts · ARCH-001/FE-013`

- `12:20 · lars+claude/OPUS · decision: input side already complete, only display gap (BUG-005) + edge-case test coverage in scope · BUG-005 · soak Q on input hardening`
- `12:18 · claude/OPUS · 5 bug tickets filed (BUG-001..005), evidence: static-read · bugs/BUG-00*.md · /bug step 1`
- `12:15 · lars · decision: wire Playwright acceptance into CI now (not deferred) · plan · AskUserQuestion`
- `12:12 · lars+claude/OPUS · decision: Playwright is already in the locked stack (ARCH-001) - no PRIN-V amendment needed; scaffolding the already-required acceptance layer · plan · ARCH-001/TEST-009`
- `12:10 · lars · decision: satisfy "reproduce as test" for layout bugs #1/#2/#3 by adding the Playwright acceptance harness (jsdom cannot test layout) · plan · AskUserQuestion`
- `12:00 · lars · scope confirmed: fix mobile bug batch (#1-#4), + cachepot spec (BUG-list #5) and botanicum spec as separate follow-ups · - · AskUserQuestion`
