# Tasks - app-settings (US-3.5)

Two disjoint lanes under one gating orchestrator (PRIN-VI). Backend lands first; frontend builds
to the API contract. TDD, red-before-green per lane (TEST-014).

## Backend lane (BE)

- [ ] BE-1 `domain/app_settings.py`: `SeasonalSettings`, `AppSettingsRepository` Protocol.
- [ ] BE-2 `domain/due.py`: add `seasonal_aware` param to `compute_due`; factor `_due_from`
      helper; OFF path ignores window + paused -> plain interval. (Tests: matrix on vs off.)
- [ ] BE-3 migration `0007_create_app_settings` (no seed); apply+rollback on SQLite + Postgres.
- [ ] BE-4 `AppSettingsModel` + repository (`get`, portable upsert `put`).
- [ ] BE-5 `application/settings.py` `AppSettingsService` (lazy default get, update).
- [ ] BE-6 `application/due.py`: `SeasonalSettingsProvider` (reads settings: window + flag),
      replace the hardcoded provider; `DueQueryService` passes the flag; N+1 bound preserved.
- [ ] BE-7 web: `SettingsResponse`/`SettingsUpdate` (month/day validation), settings router
      GET/PUT, `get_app_settings_service` dep + factory wiring.
- [ ] BE-8 tests: lazy default, round-trip + restart persistence (both engines), migration
      up/down (both engines), validation sad paths, due on/off behaviour, bounded query count.

## Frontend lane (FE)  - starts once the API contract is merged/available

- [ ] FE-1 `lib/api/settings.ts` client (types + get/update).
- [ ] FE-2 `SettingsPage` + `/settings` route + nav link: load, toggle, window inputs,
      return-to-default, save, inline feedback.
- [ ] FE-3 component/unit tests: load+render, edit+save call, return-to-default resets only the
      window inputs, error-path rendering.
- [ ] FE-4 breakpoint screenshots (FE-012); production-path verification, zero console errors
      (TEST-010).

## Gate (orchestrator)

- [ ] Both lanes green; backend suite + coverage non-regressing; frontend tests green.
- [ ] Static gates clean (ruff, mypy, import-linter, eslint, prettier, tsc, build).
- [ ] Migration apply+rollback verified on both engines (cross-engine CI leg).
- [ ] Three-reviewer gate + test-engineer re-audit.
- [ ] OpenAPI delta verified live (GET/PUT /settings; due `schedules` shape unchanged).
- [ ] Production-path screenshots committed.
