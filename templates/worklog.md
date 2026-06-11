# Worklog - `<change-name>`

Per-change trail (`TRACE-001`). Entries **newest-first**, one line each:

`time · actor · action · artifact · ref`

- **actor** = `agent-role/MODEL_TIER` (e.g. `test-engineer/HIGH`) or a person's name (`TRACE-006`)
- **ref** = the decision/rule/ADR the action traces to (`TRACE-005`); `-` if none

## AI logging guidance (`TRACE-004`)

Log an entry **when**:
- you **choose** between alternatives - log the fork + one-line why, link the ADR/decision note
- a **gate-check** runs - link the posted PASS/WATCH/FAIL block (`QG-004`); every WATCH caveat gets its own line here - these lines are the next retrospective's mandatory input
- you **stop on the circuit breaker** - state + retry count (`QG-007`)
- a **review verdict** lands - counts per severity (`REV-003`)
- you **commit** - hash + message
- the change **transitions** lifecycle state (proposed / applied / archived)
- you **deviate** from a rule (comply-or-explain, PRIN-X) or touch anything outside the spec (`SPEC-001`)

Do **NOT** log: individual file edits, reads, or routine test runs - git history and session transcripts already cover those.

**Public-repo hygiene (this file is tracked):** `specs/` is committed to the public repo. Do NOT write tracker (Plane) issue UUIDs, homelab hostnames, tokens, or personal data here - refer to work by its story id (e.g. "US-2.2") and keep tracker ids in the gitignored vault (`.claude/docs/`). *(Added 2026-06-08, sprint-2 retro: Plane ids nearly leaked into a tracked worklog.)*

---

## Entries

- `HH:MM · <actor> · change proposed · proposal.md · -`
