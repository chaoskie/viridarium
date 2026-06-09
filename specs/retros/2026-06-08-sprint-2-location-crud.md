---
title: Sprint 2 retro - Location CRUD (first real feature)
tags: [retro, sprint-2, inventory, location-crud, process]
date: 2026-06-08
scope: branch feat/us-2.2-location-crud (commits 6da28a7, aebbae4); PR #15
authors: [orchestrating Opus + maintainer]
---

# Sprint 2 retro: Location CRUD (US-2.2)

First real domain feature, and the first run under **full discipline** (the sprint-1
bootstrap exception is over). Scope: the location-crud change - 35 files, +2406 lines -
the first persisted entity, delivered as one user story across parallel backend + frontend
lanes, picked up from the inbox handoff through to a green PR awaiting maintainer merge.

## Constitution audit

| Principle | Verdict | Notes |
|---|---|---|
| PRIN-I Code quality | Followed | All source files under the 250 LOC soft ceiling; review found no dead code/unused imports; mypy strict + ruff clean |
| PRIN-II Privacy & security | Followed | 404 body asserts keys=={detail}, only the id; no PII; pre-commit leak scan + CI secret-scan green; Plane-ids scrubbed from tracked specs |
| PRIN-III Test-first | **Deviated (closed)** | red→green mandated in briefs but only trusted, not evidenced (coverage+pass+re-audit verified, not authoring order). Carry-forward from sprint-1. **Fixed forward:** TEST-014 now requires a recorded red-run |
| PRIN-IV Specs are exact scope | Followed | Review confirmed zero scope creep (no plant-guard/reassign/search/extra endpoints); exact contract match; D-009 was a docs refinement, not code scope |
| PRIN-V Stack lock-in | Followed | No new deps either lane (plain fetch over react-query was a deliberate no-amendment call) |
| PRIN-VI Story-gated iteration | Followed-with-deviation | parallel disjoint-file lanes under one gating orchestrator (zero conflict); ~780 LOC over the per-story soft budget, comply-or-explained + maintainer-approved. **Amended:** budget now per-lane when parallel |
| PRIN-VII Pipeline green | Followed | PR #15 fully green incl. the Postgres cross-engine leg + secret scan; merge state CLEAN |
| PRIN-VIII Self-verifying advancement | Followed | every agent posted a PASS/FAIL gate table; orchestrator independently re-ran the full gate, cross-checked the live OpenAPI vs the typed client, and ran a live browser smoke test before committing |
| PRIN-IX Minimal changes | Followed | other placeholder routes untouched; the 1 review MEDIUM fixed was a one-liner; CSP/font bug filed, not drive-by fixed |
| PRIN-X Comply or explain | Followed | both deviations (over-budget, Audit-Spaces deferral) recorded + maintainer-approved in the proposal |
| PRIN-XI Traceability | Followed | per-change worklog newest-first with actor/model tiers + rule refs; tracker comments at pickup + PR-ready; DoR/DoD gate results logged |

## What went well

- **Sprint-1 carry-forward closed (DoR at pickup).** The DoR gate was run and recorded in
  the proposal this time - the F-item that was unexercised in sprint 1.
- **PO decision handled without halting delivery.** Exactly one product question surfaced
  (the delete-guard, given plants don't exist yet); it produced D-009 (homeless plants +
  A/B/C delete flow) and a product-spec refinement, then delivery continued. The
  momentum-over-halts balance held - one halt, logged, resumed.
- **Verify-then-trust earned its keep.** The independent gate re-run + OpenAPI/client
  cross-check + a live smoke test (built SPA served through the backend) is the *only*
  reason the CSP/font production bug was caught - no automated gate saw it.
- **Parallel disjoint-file lanes: zero conflict again.** Backend owned `backend/`, frontend
  owned `frontend/`, the Makefile's pre-split sections needed no edit. Boundaries verified
  clean post-build.
- **Public-repo hygiene caught pre-commit.** Plane issue ids were scrubbed out of the
  tracked specs before the commit, matching the established "tracker ids live in the
  gitignored vault" convention.

## What missed

- **Test-first was trusted, not evidenced** (PRIN-III). We can prove the tests exist, pass,
  and are meaningful (re-audit) but not that they were written first. This was a known
  sprint-1 carry-forward and we still didn't capture the red.
- **A whole class of bug is invisible to our test layers.** The CSP-vs-external-assets/
  inline-script defect only appears when the *backend serves the built SPA* (production
  single-container path). vite dev has no CSP; the in-process TestClient serves no SPA. It
  was luck-of-the-verification, not a gate, that caught it.
- **The LOC budget friction repeated.** Second sprint running, second over-budget
  comply-or-explain for what is structurally unavoidable in a first-of-kind vertical slice.
- **Stale `.venv` shebang from the rename** cost the backend agent a detour (a known gotcha
  from the plant-care→viridarium rename; the agent self-recovered by rebuilding the venv).

## What to improve (applied this PR)

All five landed as amendments sliced into PR #15:

1. **TEST-014 - test-first evidence.** Build agents record the failing run (the red) in the
   worklog before the green commit. (`rules/testing.md`, `rules/00-constitution.md` PRIN-III
   note, `templates/agent-brief-preflight.md` step 5, `templates/dod.md` §3.)
2. **Per-lane LOC budget.** When one story runs as parallel disjoint lanes, the ~400-500
   soft budget is measured per lane; the 1000 hard ceiling stays per story.
   (`rules/00-constitution.md` PRIN-VI, `rules/specs-scope.md` SPEC-004.)
3. **Production-path UI verification.** DoD now requires UI stories to be verified via the
   backend-served built SPA with zero console errors (`TEST-010`), catching CSP-class bugs.
   (`templates/dod.md` §3.)
4. **Public-repo worklog hygiene.** Worklog template now warns to keep tracker ids/hostnames
   out of tracked specs. (`templates/worklog.md`.)
5. **Amendments table** updated with both fork decisions (constitution Change Log).

## Forks resolved

- **Test-first evidence:** maintainer chose **require a lightweight red-run proof** (over
  trust+coverage). → TEST-014.
- **LOC budget for parallel vertical slices:** maintainer chose **per disjoint lane when
  parallel** (over per-story + first-of-kind allowance, or leave-as-is). → PRIN-VI / SPEC-004.

## Carry-forward action items

- [ ] **US-2.1 must demonstrate TEST-014** (recorded red-run) - the real test of the new rule.
- [ ] Stand up the **Playwright/axe/perf infra story**; wire it to run against the
      backend-served build so `TEST-010` enforces the production-path check automatically
      (turns improvement #3 from manual to gated).
- [ ] Fix the **CSP/font + inline-theme-script bug** (filed high) before any "v0.1 usable" claim.
- [ ] Bump CI actions off **Node 20** before 2026-06-16 (filed low).
- [ ] Harden the shared **Modal** (focus-trap + restoration) when US-2.1 reuses it (filed low).
- [ ] At merge: move US-2.2 to Done with the merge SHA; `spec-archive` the change + write the
      change-index entry (TRACE-002).
