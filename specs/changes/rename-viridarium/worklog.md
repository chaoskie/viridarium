# Worklog - `rename-viridarium`

Per-change trail (`TRACE-001`). Entries newest-first.

`time · actor · action · artifact · ref`

---

## Entries

- `19:08 · rename-agent/OPUS · screenshot of renamed app shell captured · docs/design/themes/implemented-viridarium.png · T19`
- `19:07 · rename-agent/OPUS · docker smoke PASS: build ok, container up, /api/v1/health=ok, / serves SPA with virid+arium wordmark + viridarium.theme key; container+image removed · Dockerfile, docker-compose.yml · T17/QG-004`
- `19:06 · rename-agent/OPUS · frontend gates PASS: eslint clean, prettier clean, tsc clean, 15 vitest tests pass (run against existing node_modules; npm ci blocked by pre-existing root-owned node_modules) · frontend/* · T16/QG-001`
- `17:05 · rename-agent/OPUS · backend gates PASS: lint, format-check, mypy (25 files), import-linter (3 contracts kept), coverage 97.5% (13 tests), pip-audit clean (2 ignored) · backend/* · T16/QG-001/QG-002`
- `17:04 · rename-agent/OPUS · package + import + config rename applied; uv.lock regenerated (viridarium-backend) · backend/, frontend/, Makefile, Dockerfile, docker-compose.yml, README*.md, .github/* · T2-T15`
- `17:00 · rename-agent/OPUS · deviation logged: deliberate survivors kept - "plantcare" PostgreSQL DB identifier (CI + compose) and generic "plant care" prose are descriptions, not the product name (PRIN-X comply-or-explain) · quality-gates.yml, docker-compose.yml, CLAUDE.md · SPEC-001`
- `16:58 · rename-agent/OPUS · preflight: python 3.12.3, uv 0.11.6, node v24.13.1, npm 11.8.0. MISMATCH flagged: local node v24 vs CI/Dockerfile pin node 20.19 - does not change any committed artifact (lockfileVersion 3 / npm 11 match), so proceeded · - · agent-brief-preflight.md`
- `16:55 · rename-agent/OPUS · change proposed · proposal.md · -`
