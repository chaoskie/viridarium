# Security (`SEC-*`)

**Enforces:** the teeth of [[00-constitution#PRIN-II Privacy & Security|PRIN-II]] for a **trusted-network, no-auth-in-v1** self-hosted app - the documented trust boundary, secure-by-default posture, input validation, secrets handling, privacy-first logging, dependency CVE policy, the end-of-feature security review, and the security-headers baseline. Consumed by the security-reviewer agent, developers, and CI.

**Design posture:** v1 has **no user authentication** by design. The app targets deployment behind a trusted boundary (LAN, VPN, or an authenticating reverse proxy). The security rules therefore protect the trust boundary, the data, and the supply chain rather than implementing in-app auth. Any future auth feature is **opt-in** and arrives via an ADR (ARCH-010); it does not weaken these rules.

---

## Trust boundary & access posture

### SEC-001 — Document the trust boundary; no implicit exposure
Every deployment-facing surface MUST have a documented trust boundary: what is assumed authenticated/trusted *outside* the app (reverse proxy, LAN, VPN) and what the app assumes about its callers. The app MUST NOT silently expose privileged or destructive operations as if the network were public. New endpoints state their exposure assumption; anything that would be dangerous on an open network is flagged in the proposal.
*Targets:* security-reviewer, developers, design work.

### SEC-002 — Authorization is out of scope in v1, by design (RETIRED-as-auth, repurposed)
There are no roles or per-route authorization in v1; all callers within the trust boundary are equally privileged (SEC-001). Therefore destructive/bulk operations MUST be deliberate and explicit in the API design (clear verbs/paths, no surprising side effects), since there is no auth layer to lean on. The moment any access-control requirement appears, it is an auth feature → ADR per SEC-003.
*Targets:* security-reviewer, developers.

### SEC-003 — No auth in v1; secure-by-default runtime posture
Authentication is **not implemented in v1** (the source's OIDC/Keycloak/JWT/session requirements do not apply). Instead, the runtime MUST be secure-by-default:
- **Bind address:** default to a safe bind (configurable; do not default-bind a privileged or destructive admin surface to `0.0.0.0` without it being a documented, deliberate choice).
- **CORS:** locked down by default (no wildcard `*` with credentials); allowed origins are explicit configuration, not hardcoded permissive defaults.
- **No secrets in the repo** (SEC-006); no PII in logs (SEC-007).
- **Security headers** present (SEC-011).
Any future authentication/authorization capability is **opt-in**, introduced via an ADR (ARCH-010), and MUST NOT silently change the default no-auth posture.
*Targets:* security-reviewer, developers.

## Input & data

### SEC-004 — Server-side input validation everywhere
Input is validated **server-side** at every boundary: API payloads (Pydantic v2 models), query/path params, and any file or import path. Data from untrusted sources is validated before use - regardless of any client-side validation.
*Targets:* developers, security-reviewer.

### SEC-005 — No raw SQL, no dynamic execution
Persistence goes through SQLAlchemy with bound parameters - no string-interpolated SQL, no f-string queries. User input MUST NOT reach dynamic execution of any kind (raw SQL string-building, `eval`/`exec`, dynamic import, attribute injection). This is the primary injection defense given there is no auth layer.
*Targets:* developers, code-reviewer, security-reviewer.

### SEC-006 — Secrets
No secrets in code, ever - environment variables / external config only; connection strings (`DATABASE_URL`) and any consumer credentials never hardcoded. `.env*` and credential files are **protected from agent edits** (enforced via `.claude/settings.json` deny rules; review red flag otherwise). Agents never read `.env*`/credential files into context.
*Targets:* security-reviewer, all agents.

### SEC-007 — Sensitive data and PII stay out of logs
Sensitive fields and any personal data NEVER appear in logs or error responses. Production logs contain no secrets, no `DATABASE_URL`, no full request bodies, and no raw stack traces leaked to API responses. Because the repo is public and self-hosted, logging hygiene is also about not baking sample PII into fixtures or examples.
*Targets:* developers, security-reviewer.

## Audit & observability

### SEC-008 — Privacy-first event logging (per-story space)
Every **state-changing route** (create/update/delete on plants, schedules, etc.) emits ≥1 structured event on success; failure paths, input-validation failures, and tampering indications are logged at **Warning or higher**. Asserted per story (opt-out needs written justification in the proposal).

**Privacy-first field schema** - events identify the actor by **pseudonymous context only** (e.g. source IP / client label where proportionate), never personal data:
`{ event, source, result, timestamp }`. With no user accounts in v1 there is no user identity to log; do not invent one. If auth is added later, the actor field is extended via the same ADR that adds auth.
*Targets:* test-engineer, security-reviewer, developers.

## Vulnerabilities

### SEC-009 — CVE policy
No CVSS > 7.5 in a release unless explicitly accepted and documented. Every dependency-audit ignore/allow entry (`pip-audit` ignore, `npm audit` advisory) carries a justification comment **and a revisit date**; entries past their revisit date are flagged (CI-005 scans daily).
*Targets:* security-reviewer, ci, td workflow.

### SEC-010 — End-of-feature security review
Before a feature ships, the **security-reviewer** runs a dedicated pass over the feature surface: OWASP-relevant mitigations (injection, broken access posture vs the documented trust boundary, security misconfiguration, vulnerable dependencies), input validation at all entry points, no raw SQL / dynamic execution, secret/credential handling, secure-by-default posture (bind/CORS), no PII in logs, and headers (SEC-011). Output: structured findings per REV-003. **Open BLOCKING findings block the release.**
*Targets:* security-reviewer, security-review workflow, DoD template.

### SEC-011 — Security headers baseline
Responses carry: `Content-Security-Policy` (no inline script/style), `X-Content-Type-Options: nosniff`, `Referrer-Policy: strict-origin-when-cross-origin`, `Permissions-Policy` denying unused capabilities. Set centrally (middleware) so every response is covered.
*Targets:* developers, security-reviewer, test-engineer.

## Runtime

### SEC-012 — Container hygiene
If shipped as a container, it does not run as root; image tags are never `latest` or empty (pin digests per CI-006); privilege escalation is disabled. Exceptions documented per service. The default `docker run` posture is safe for trusted-network deployment.
*Targets:* ci, security-reviewer.
