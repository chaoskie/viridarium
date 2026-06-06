# Contributing

Thanks for your interest in contributing! This project is maintained by a solo maintainer with AI assistance, developed fully in the open. A few ground rules keep that sustainable.

## Scope first

Before opening a feature PR, check the project vision in the README and open an issue or discussion first. Features outside the documented scope will be declined, even when well built. "No is temporary, yes is forever."

## Development setup

See the README quickstart. In short: Python 3.12+ and Node 20+ are required, `make dev` runs both backend and frontend, `make quality-gates` runs every deterministic check that CI runs.

## Workflow

- Work happens spec-first: changes of any substance get a short proposal in `specs/changes/<name>/` before code. Small fixes can go straight to a PR.
- Tests precede implementation. New code needs tests; CI enforces coverage on the diff.
- Run `make quality-gates` locally before pushing. CI runs the same gates; a red pipeline does not merge.

## Commits

- [Conventional Commits](https://www.conventionalcommits.org/): `feat:`, `fix:`, `docs:`, `chore:`, `refactor:`, `test:`. Breaking changes use `!` or a `BREAKING CHANGE:` footer.
- Imperative subject, 72 characters max.
- Releases are automated from commit history (release-please), so commit types matter.

## AI assistance policy

AI-assisted contributions are welcome under these conditions:

1. **Disclose it** in the PR description for any non-trivial change. Trivial autocomplete does not need disclosure.
2. **You are accountable.** You must understand, have tested, and be able to maintain the code you submit. "The AI wrote it" is not a review response.
3. Undisclosed or unreviewed AI bulk submissions will be closed without detailed review.

This project itself is largely built with AI assistance, in the open, with every change reviewed and gated. The policy is about ownership, not about tools.

## Issues

- Use the issue forms; they ask for the info needed to act (version, deploy method, logs).
- Support questions go to Discussions, not issues.
- Security issues: see [SECURITY.md](SECURITY.md). Never open a public issue for a vulnerability.

## Code standards

The enforceable standards live in `rules/` and are checked by `make quality-gates` plus AI-assisted review. Highlights: hexagonal architecture (domain code imports no framework), strict typing on domain and application layers, 80% coverage on new code.
