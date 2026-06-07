# Agent brief: preflight section (include in every build-agent brief)

Before writing any code:

1. Report the toolchain you find: `python3 --version`, `uv --version`, `node --version`, `npm --version` (whichever apply to your story).
2. Compare against what the repo pins: CI workflow images/setup actions, Dockerfile base stages, lockfile versions (`package-lock.json` lockfileVersion and generator, `uv.lock`).
3. Flag any mismatch in your report BEFORE building on it; if the mismatch would change an artifact you commit (a lockfile, a pin), stop and ask the orchestrator.
4. State which gate commands you will run for your story and confirm they exist in the Makefile.

Rationale: retro 2026-06-07, the npm 10/11 lockfile skew was found at docker build time instead of story start.
