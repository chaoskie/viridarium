---
description: Diagnose and fix a red pipeline - without ever weakening the gates
---
Pipeline medic: $ARGUMENTS

PRIN-VII: every push is green; there are no "pre-existing failures". Runner is GitHub Actions (`CI-001`).

1. Identify the failing job (`CI-001`: lint / test / security / build) and the first real error - not the cascade.
2. Classify: code defect → fix via TDD (`PRIN-III`); flaky test → fix the test for independence (`TEST-006`), never delete it; infra/config → fix the workflow config; CVE → handle per `SEC-009` (fix, or justified audit-ignore WITH revisit date); dual-engine failure → fix portability (`ARCH-011`).
3. **Never weaken a gate to get green:** no coverage-threshold lowering, no test deletion/skip, no permissive CORS or disabled headers to dodge a security check, no unpinning (`CI-006`), no removing budget checks. Gate changes require an ADR.
4. Circuit breaker (`QG-007`): 3 retries on the same fix / 5 distinct failures → stop, report state, escalate.
5. Log diagnosis + fix to the worklog (`TRACE-003`).
