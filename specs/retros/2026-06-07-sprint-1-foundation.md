---
title: Sprint 1 retro - foundation bootstrap
tags: [retro, sprint-1, foundation, process]
date: 2026-06-07
scope: commits 407f0a2..c431983 (root through Foundation complete)
authors: [orchestrating agent + maintainer]
---

# Sprint 1 retro: foundation

First run of the hybrid workflow (rules scaffold port + ticket discipline + deterministic gates + autonomous build agents). Scope: 4 commits, 88 files, ~10.4k insertions; the entire Foundation module (5 stories) from empty directory to gated, dockerized walking skeleton.

## Constitution audit

| Principle | Verdict | Notes |
|---|---|---|
| PRIN-I Code quality | Followed | Gates enforce; agents removed their own dead code (unused session helper) |
| PRIN-II Privacy & security | Followed | Leak audit before first commit; secure-by-default posture; CVE bumps during scaffold |
| PRIN-III Test-first | **Deviated** | Walking-skeleton stories wrote tests alongside, not strictly red-green first. Acceptable for scaffolds; real domain stories (E2/E3) must show test-first evidence |
| PRIN-IV Specs are exact scope | **Deviated** | Release automation (a separate planned story) was delivered inside the ci-and-docker change. Outcome fine, but scope merge was decided in the brief, not in a proposal |
| PRIN-V Stack lock-in | Followed | D-001 decision ratified before any code |
| PRIN-VI Story-gated iteration | **Deviated** | Backend and frontend scaffold stories ran in parallel (disjoint files), both directly on main. Logged as bootstrap exception; see fork F1 |
| PRIN-VII Pipeline green | Followed (locally) | No remote CI yet (repo pending name); `make quality-gates` green at every commit |
| PRIN-VIII Self-verifying advancement | Followed | Agents posted PASS/FAIL gate tables; orchestrator independently re-ran gates before each commit |
| PRIN-IX Minimal changes | Followed | npm-11 finding fixed by pinning, not by a drive-by lockfile regeneration |
| PRIN-X Comply or explain | Followed | Deviations carry written rationale (bootstrap exception, pip-audit accepted advisory with revisit date, npm pin) |
| PRIN-XI Traceability | Followed | Per-change worklogs, tracker comments at pickup/completion with commit SHAs |

## What went well

- **The port recipe held.** The scaffold's Claude Code port doc translated cleanly; one agent produced the full rules/agents/commands tree in one pass, and the stack rewrite (Kotlin/Angular to FastAPI/React) preserved rule IDs and gate semantics.
- **Research before commitment paid off.** The landscape sweep shaped real product differentiators (seasonal schedules, ICS, no-login) and validated the SQLite-default call before any code locked it in.
- **Disjoint-file parallel agents were fast and conflict-free.** Backend + frontend scaffolds built simultaneously; the only merge point (Makefile) was designed as an append seam in advance.
- **Deterministic gates caught real issues during build**, not at review: three CVE-driven dependency bumps, an import-linter violation avoided by design, the SPA-fallback edge case found by its own test.
- **Theme-token layer decoupled the design decision from delivery.** Five theme candidates are waiting on a PO pick while the build advances on neutral tokens.
- **Independent re-verification caught nothing false** (agents' green claims were accurate) but is cheap and stays: trust, then verify.

## What missed

- **Environment skew surfaced late.** The frontend lockfile was generated with npm 11; node:20's npm 10 rejects it. Found only at docker build time. A "toolchain versions" preflight in scaffold briefs would have caught it at story start.
- **Story scope merged without a proposal step.** Release automation rode along in the ci-and-docker brief. Right outcome, wrong recording: the merge should have been one line in the change proposal ("delivers story X and story Y because the workflows are one artifact").
- **Shell cwd drift** in the orchestrator wasted a cycle (`make` invoked from frontend/). Trivial, but the kind of friction worth a habit fix (absolute paths in orchestration commands).
- **No DoR/DoD checklists were formally instantiated** for these stories even though the templates exist. For scaffolds the cost was zero; for E2+ stories the DoR gate (INVEST check) should actually run at pickup.

## What to improve (next sprint)

1. **Resolve fork F1 and amend PRIN-VI accordingly** (see Forks).
2. **Brief template addition** for build agents: a preflight section ("report node/python/npm/uv versions; flag any mismatch with lockfiles/CI images before writing code"). Saved to `templates/agent-brief-preflight.md`.
3. **Run the DoR gate at story pickup** starting with the first E2 story; record it in the change proposal.
4. **PR flow starts at repo creation**: branch per story, PR with template, branch protection on the quality-gates workflow, maintainer merges. The bootstrap exception ends there.
5. **npm standardization** per fork F2.

## Forks for the maintainer (pending)

- **F1 - story parallelism.** PRIN-VI says one story at a time. This sprint ran two scaffold stories in parallel with disjoint file ownership and it worked well.
  - (a) Keep strict serial story gating.
  - (b) Amend: independent stories MAY run in parallel when file ownership is disjoint and a single orchestrator gates and commits the results. (Recommended)
- **F2 - npm toolchain.** Lockfile needs npm 11; node 20's bundled npm is 10.
  - (a) Keep the npm 11 pin in CI + Dockerfile, add an `engines` advisory in package.json. (Recommended, current state)
  - (b) Regenerate the lockfile with npm 10 so stock node 20 works out of the box.

## Carry-forward action items

- [ ] Apply F1/F2 resolutions (constitution amendment + package.json engines or lockfile regen)
- [ ] Create GitHub repo on name pick: branch protection, Discussions on, secret scanning + push protection, update OWNER/REPO placeholders
- [ ] Apply chosen theme tokens to frontend/src/styles/tokens.css
- [ ] First E2 story (US-2.2 Location CRUD is the natural smallest start) with full DoR + test-first evidence + PR flow
- [ ] Wire diff-cover and OpenAPI-drift Makefile targets into CI (flagged in ci-and-docker follow-ups)
- [ ] Revisit pip-audit accepted advisory PYSEC-2026-161 by 2026-09-01
