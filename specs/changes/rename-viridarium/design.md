# Design brief - `rename-viridarium`

## Approach

Pure mechanical rename, no behavioural change. Two distinct token classes are handled
separately so prose is never collateral-damaged by import rewrites:

1. **Code identifier `plant_care`** (Python package / module path). Replaced wholesale
   with `viridarium` in every `.py` import, `pyproject.toml` module references,
   `alembic.ini` `script_location`, Makefile targets, and the Dockerfile `CMD`. The
   package directory is moved with `git mv` to preserve history.
2. **Brand / display strings** (`plant-care`, `plantkeep`, titles). Replaced
   case-by-case with `Viridarium` (prose / titles) or the lowercase `viridarium`
   wordmark, leaving generic descriptive phrases ("plant care web app") intact where they
   read as descriptions, not the product name.

## Wordmark

The AppShell wordmark keeps its brand-tile styling. The old `plant`+`keep` split (accent
on `keep`) becomes `virid`+`arium` with the accent (`text-accent`, terracotta) on the
`arium` half. The emoji brand tile and all Tailwind classes are unchanged.

## Theme storage key

`plant-care.theme` -> `viridarium.theme` in two synced places: `themeController.ts`
(`THEME_STORAGE_KEY`) and the inline pre-paint script in `index.html`. The controller
tests reference the exported constant, so they follow automatically. (Existing users would
lose their stored theme preference and fall back to the default `terracotta`; acceptable
for a pre-alpha pre-publish rename.)

## Lockfiles

`uv.lock` is regenerated via `uv lock` (package renamed `plant-care-backend` ->
`viridarium-backend`). `package-lock.json` carries only the `name` field, edited in place
(no dependency graph change).

## Risk / rollback

Mechanical and fully covered by the existing quality gates plus a docker smoke test. No
data migration, no API contract change (the `/api/v1` paths and health payload are
untouched). Rollback is a revert.
