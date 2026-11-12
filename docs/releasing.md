# Releasing

How versions are chosen, what gates a release, and what a release publishes. Records
decisions D-012 and D-014 from the [decision log](decisions/README.md).

## Mechanics

- Releases are automated from Conventional Commits by release-please
  (`.github/workflows/release-please.yml`). Merging its release PR creates the tag, the
  GitHub release and the CHANGELOG entry. Releases are immutable.
- Publishing a release triggers two workflows:
  - `publish.yml` builds the multi-arch image and pushes it to
    `ghcr.io/chaoskie/viridarium`, tagged `X.Y.Z`, `X.Y`, `X` and `latest`.
  - `device-matrix.yml` runs the acceptance suite across the mobile device matrix, see
    [testing-e2e.md](testing-e2e.md).
- No image is published before the first release. Until then, deploy by building from a
  checkout (`build: .` in `docker-compose.yml`).

## Version policy (D-012)

- **Minor bump when an epic completes** (all its stories merged and gated). The epic is
  the unit at which the app gains a coherent user-facing capability.
- **Patch bump for deploy-worthy standalone fixes** between epics. Trivial fixes
  accumulate until something is worth deploying.
- **No tag per merge.** Story-sized PRs do not consume version numbers.
- **v0.1.0** is the "first usable" milestone: care schedules, logging and due computation
  plus the Today view. Everything before it is pre-release history.
- **Pre-1.0:** breaking API changes are allowed in minor bumps and are listed under a
  Changed/Breaking heading in the changelog.
- **1.0.0** only when the open API is declared stable for home-automation integrators.

A release PR that proposes a version outside this policy (for example 1.0.0 as the first
release) must not be merged; fix the release-please configuration first.

## Soak before a public release (D-014)

A milestone or first public release is not tagged the moment its features are merged:

1. Deploy a build of the candidate commit to a real instance on a trusted network: built
   from source, pinned to that commit, with the data volume backed up.
2. Use it for real for about a week.
3. File what turns up, fix it test-first, redeploy and continue the soak.
4. Tag only when the instance has proven sufficient and the bug list is clean.
5. After the release, switch that instance from the source build to the published
   versioned image on the same volume, so its data carries over.

Why: the tag fires the image publish and the GitHub release, which are hard to walk
back. A week of daily use surfaces problems that tests and a smoke pass do not, because
the app is used away from the desk, on a phone, on actual plants. The trusted-network
posture ([D-003](decisions/D-003-no-auth-trust-boundary.md)) makes such a soak safe
without authentication.

## Upgrading an installation

The container applies its database migrations on every start, before the server binds
(see the [README](../README.md)). Open design work on backups, opt-out and update
tooling is collected in [research/upgrade-path.md](research/upgrade-path.md).
