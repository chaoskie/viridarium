# Worklog - `<change-name>`

Per-change trail (`TRACE-001`). Entries **newest-first**, one line each:

`time · actor · action · artifact · ref`

- **actor** = `agent-role/MODEL_TIER` (e.g. `test-engineer/HIGH`) or a person's name (`TRACE-006`)
- **ref** = the decision/rule/ADR the action traces to (`TRACE-005`); `-` if none

## AI logging guidance (`TRACE-004`)

Log an entry **when**:
- you **choose** between alternatives - log the fork + one-line why, link the ADR/decision note
- a **gate-check** runs - link the posted PASS/FAIL block (`QG-004`)
- you **stop on the circuit breaker** - state + retry count (`QG-007`)
- a **review verdict** lands - counts per severity (`REV-003`)
- you **commit** - hash + message
- the change **transitions** lifecycle state (proposed / applied / archived)
- you **deviate** from a rule (comply-or-explain, PRIN-X) or touch anything outside the spec (`SPEC-001`)

Do **NOT** log: individual file edits, reads, or routine test runs - git history and session transcripts already cover those.

---

## Entries

- `HH:MM · <actor> · change proposed · proposal.md · -`
