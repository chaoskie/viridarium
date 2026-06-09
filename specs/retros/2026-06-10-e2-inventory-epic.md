---
title: E2 Plant Inventory epic retro
tags: [retro, epic-e2, inventory, process]
date: 2026-06-10
scope: main d3d4092..1ce47a8 (US-2.2 #15, US-2.1 #17, US-2.4 #18, US-2.3 #19)
authors: [orchestrating Opus + maintainer]
---

# E2 (Plant Inventory) epic retro

The whole inventory epic in one run: 4 stories, 5 PRs (one auto-closed + superseded), all
merged to main; 101 files, +10.6k. First run with autonomous PO-authorized merging and the
sprint-2 amendments (TEST-014 red-run evidence, per-lane budget, production-path verification)
in force. A stack amendment (python-multipart) and the project's first file-upload surface.

## Constitution audit

| Principle | Verdict | Notes |
|---|---|---|
| PRIN-I Code quality | Followed | Gates green throughout; one LOW (PlantsPage 456 LOC over the 250 soft ceiling, pre-existing + grew, filed) |
| PRIN-II Privacy & security | Followed-with-gap | Photos security review CLEAN (sniff authoritative, traversal-safe, no-PII, cross-plant 404); 404/413/415 id-only. **Gap:** SEC-008 structured logging unmet across the whole epic (standing-duty deviation, see forks) |
| PRIN-III Test-First | Followed | TEST-014 red-runs recorded for all 4 stories (incl. the SQLite SET-NULL red before the engine pragma) - the sprint-2 carry-forward fully exercised |
| PRIN-IV Specs are exact scope | **Deviated→corrected** | US-2.1 build agent invented enum values (`glass/metal/concrete`, `low/medium`) vs product-spec §3 and mislabeled them "spec wire form"; caught by the orchestrator verify + OpenAPI cross-check, corrected pre-merge. Net-clean after correction; the catch is the point |
| PRIN-V Stack lock-in | Followed (amended) | python-multipart added via ADR-010, PO-approved, recorded in ARCH-001; Pillow declined |
| PRIN-VI Story-gated iteration | Followed | Each story own branch/PR/gate; parallel disjoint lanes; per-lane budget honored (US-2.3 backend ~600 LOC over the per-lane soft cap, comply-or-explained, under the 1000 hard ceiling) |
| PRIN-VII Pipeline green | Followed | Every PR merged on a fully green pipeline incl. the dual-engine (SQLite+Postgres) legs + secret scan |
| PRIN-VIII Self-verifying | Followed | Per-lane PASS/FAIL gates; orchestrator independent full-gate re-run + live OpenAPI/client cross-check + production-path smoke before every merge |
| PRIN-IX Minimal changes | Followed | The two cross-cutting touches (engine.py FK pragma; PlantService.delete photo cleanup) were necessary + justified; no drive-bys |
| PRIN-X Comply or explain | Followed | Every deviation recorded (the dep amendment, per-lane over-budget, API-002 hand-written client, Audit-Spaces deferral); the SEC-008 over-claim was corrected post-review |
| PRIN-XI Traceability | Followed | Per-change worklogs newest-first with actor/model tiers; ticket transitions In Progress→Done with merge SHAs + closing comments |

## What went well

- **Architect-first paid off twice in hard currency.** The architect passes caught two real
  infra hazards *before any code*: the SQLite `PRAGMA foreign_keys=ON` gap (without which
  SET-NULL/CASCADE silently no-op on the default engine - a cross-engine divergence) and the
  `python-multipart` requirement (a blocking stack amendment). Both would have been painful
  discoveries mid-build or post-merge.
- **TEST-014 (sprint-2 amendment) genuinely worked.** Every story recorded a real red-before-
  green, including the satisfying SQLite SET-NULL red (`assert 1 is None`) that proved the FK
  pragma was load-bearing. Test-first is now auditable from the worklogs, not trusted.
- **Verify-then-trust caught what every automated gate passed.** The invented-enum SPEC-001
  deviation cleared ruff, mypy-strict, 99% coverage, and the test suite (the tests iterated the
  wrong enum happily) - only the orchestrator's OpenAPI-vs-spec cross-check flagged it. The
  layered defense (independent gate re-run + contract cross-check + prod-path smoke) is the
  reason the merges are trustworthy.
- **Production-path security smoke = high-confidence verification.** For photos, booting the
  backend-served build and exercising real uploads + every reject lane + traversal-safe naming
  + plant-delete file cleanup gave confidence no unit test fully equals.
- **The PRIN-V gate was handled correctly.** The dep amendment was surfaced to the PO, approved,
  recorded as ADR-010 + in the public ARCH-001 table - not assumed.
- **Autonomous PO-authorized merging was smooth.** 5 green merges, the board moved in lockstep
  (In Progress→Done with SHAs), tech-debt filed at each step rather than dropped.
- **Per-story re-audit + code-review caught real gaps:** US-2.4's missing hook error-test and
  the view-reset MEDIUM; US-2.1's FK-untested-on-Postgres HIGH (fixed with a cross-engine test).

## What missed

- **The stacked-PR snag.** Squash-merging #15 then `--delete-branch` on its base auto-CLOSED the
  stacked #16 (GitHub closes PRs whose base branch is deleted), forcing a rebase-onto-main +
  reopen as #17. Avoidable operational friction; a known GitHub behavior we walked into.
- **A build agent went off-spec on domain vocabulary.** US-2.1 invented enum values rather than
  using product-spec §3 verbatim - and labeled them as if they were the spec's. The brief didn't
  pin "use the exact spec vocabulary; never invent or extend a domain enum."
- **A proposal over-claimed a control.** US-2.3's proposal asserted SEC-008 structured events
  were emitted; they weren't (nor anywhere in the project). Caught at review, corrected. Proposals
  should not assert controls that aren't built.
- **SEC-008 structured logging is unmet epic-wide (and project-wide).** A standing duty silently
  unsatisfied story after story. The per-story logging duty is real on paper, dead in practice.
- **FK runtime behavior was untested on Postgres** until the US-2.1 review HIGH - the integration
  conftest pins SQLite, so the Postgres CI leg only ran DDL. Partially addressed by a targeted
  cross-engine test; the full dual-engine integration harness is still tech-debt.

## What to improve (applied this retro)

1. **Stacked-PR operational rule** → `process/agent-orchestration.md` gotcha: when PRs are
   stacked, do NOT `--delete-branch` the base on merge of the lower PR (it closes the child);
   merge bottom-up then rebase the child onto main and retarget BEFORE deleting, or use a
   merge-commit. Recorded.
2. **Exact-spec-vocabulary brief rule** → `templates/agent-brief-preflight.md`: build agents use
   the product-spec's domain vocabulary (enum values, names) VERBATIM; inventing or extending a
   domain enum/field is a SPEC-001/PRIN-IV violation, not a judgment call.
3. **DoD claims-audit** → `templates/dod.md`: every security/logging/perf control the proposal
   asserts is verified actually-implemented at DoD, or the proposal is corrected - no aspirational
   claims left standing (born from the SEC-008 over-claim).

## Forks for the human

- **SEC-008 structured logging** (unmet epic-wide). Options:
  - (a) Build an observability/logging slice project-wide as a dedicated story now, before more
    features pile on the gap.
  - (b) Formally mark SEC-008 logging as deferred-to-a-named-observability-story in the rules, so
    proposals stop asserting it as met (honesty) - then build it when the story is scheduled.
  - (c) Leave the per-story duty as-is (status quo; keeps silently slipping).
  - **Recommendation: (a)+(b)** - file the observability story (done, backlog) AND note SEC-008 as
    deferred-until-then. Pending PO confirm.

## Carry-forward action items

- [ ] PO call on the SEC-008 fork; if (a)/(b), the observability story is filed and SEC-008 gets a deferred-note.
- [ ] Full dual-engine integration harness (run the whole integration suite on Postgres in CI, not just FK behavior) - filed.
- [ ] Upload **body-size limit** before multipart spooling (security defense-in-depth) - filed.
- [ ] **CSP prod bug** (fonts/theme-script blocked when the backend serves the SPA) - fix before any "v0.1 usable" claim.
- [ ] PlantsPage refactor / a `cover_url` on `PlantResponse` (removes the CoverThumb N+1) - filed.
- [ ] Node-20 CI action bump before 2026-06-16 - filed.
- [ ] Review **Fable 5**'s independent cross-epic findings (running in parallel) and action any genuine improvements.

## Next

E2 is complete. v0.1 remaining: **E3** (care schedules + logging + due computation) and **E4.1**
(Today view). Due computation will reuse the `archived` flag (D-009 / US-2.4 forward-link) and
the existing repository-port template.
