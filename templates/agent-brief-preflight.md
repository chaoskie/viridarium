# Agent brief: preflight section (include in every build-agent brief)

Before writing any code:

1. Report the toolchain you find: `python3 --version`, `uv --version`, `node --version`, `npm --version` (whichever apply to your story).
2. Compare against what the repo pins: CI workflow images/setup actions, Dockerfile base stages, lockfile versions (`package-lock.json` lockfileVersion and generator, `uv.lock`).
3. Flag any mismatch in your report BEFORE building on it; if the mismatch would change an artifact you commit (a lockfile, a pin), stop and ask the orchestrator.
4. State which gate commands you will run for your story and confirm they exist in the Makefile.

During the work (test-first evidence, `TEST-014`):

5. Write the tests first and **paste the failing run (the "red") into the change worklog** - the test names + the failing assertion/error - BEFORE writing the implementation that turns them green. Then implement to green. The orchestrator records this as the PRIN-III evidence; a worklog with no red-before-green is a deviation.

6. **Use the spec's domain vocabulary verbatim.** Enum values, field names, and status terms come from `docs/product-spec.md` (and the change's design) EXACTLY as written. Inventing or extending a domain enum/field (e.g. adding pot materials the spec doesn't list, renaming light levels) is a **SPEC-001 / PRIN-IV violation**, not a judgment call - and never label invented values as "the spec wire form." If the spec seems wrong or incomplete, STOP and raise it; do not improve it silently.

Rationale: preflight 1-4 from retro 2026-06-07 (npm 10/11 lockfile skew found at docker build time); step 5 from retro 2026-06-08 (test-first mandated but only trusted, not evidenced); step 6 from the E2 retro 2026-06-10 (a build agent invented enum values + mislabeled them, caught only by the orchestrator's OpenAPI-vs-spec cross-check).
