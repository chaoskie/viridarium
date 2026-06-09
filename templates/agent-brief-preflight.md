# Agent brief: preflight section (include in every build-agent brief)

Before writing any code:

1. Report the toolchain you find: `python3 --version`, `uv --version`, `node --version`, `npm --version` (whichever apply to your story).
2. Compare against what the repo pins: CI workflow images/setup actions, Dockerfile base stages, lockfile versions (`package-lock.json` lockfileVersion and generator, `uv.lock`).
3. Flag any mismatch in your report BEFORE building on it; if the mismatch would change an artifact you commit (a lockfile, a pin), stop and ask the orchestrator.
4. State which gate commands you will run for your story and confirm they exist in the Makefile.

During the work (test-first evidence, `TEST-014`):

5. Write the tests first and **paste the failing run (the "red") into the change worklog** - the test names + the failing assertion/error - BEFORE writing the implementation that turns them green. Then implement to green. The orchestrator records this as the PRIN-III evidence; a worklog with no red-before-green is a deviation.

Rationale: preflight 1-4 from retro 2026-06-07 (npm 10/11 lockfile skew found at docker build time); step 5 from retro 2026-06-08 (test-first was mandated but only trusted, not evidenced).
