---
description: End-of-feature security review - blocking findings block the release
---
End-of-feature security review for: $ARGUMENTS

Delegate to the security-reviewer subagent to run the full `SEC-010` pass over the feature surface:
1. OWASP-relevant mitigations on every new/changed endpoint and input path (injection, security misconfiguration, broken access posture vs the documented trust boundary).
2. Dependency CVEs (`SEC-009`): current `pip-audit` / frontend audit results; ignore/allow entries valid (justification + unexpired revisit date).
3. Boundary integrity: validation at every entry point (`SEC-004`), no raw SQL / dynamic execution (`SEC-005`), anti-corruption respected (`ARCH-009`).
4. Secrets and logs: nothing sensitive in code, logs, or error responses; no PII in logs (`SEC-006/007`).
5. Trust-boundary posture: documented exposure (`SEC-001/002`), secure-by-default bind + locked-down CORS, no-auth posture not silently changed (`SEC-003`).
6. Headers (`SEC-011`) and events on state changes (`SEC-008`).

Output a structured report per `REV-003`. **Any open BLOCKING finding blocks the release - file it, no exceptions.** Log the verdict to the worklog (`TRACE-003`).
