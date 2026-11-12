# D-013: Global seasonal-aware care toggle

Status: ratified, 2026-06-15. The rule itself is specified in
[product-spec](../product-spec.md) section 3; this note records the reasoning.

## Decision

One app-wide switch, on by default:

- **On:** the winter window plus each schedule's `winter_interval_days` and `dormancy`
  apply to due computation.
- **Off:** the due engine ignores both the winter interval and `paused` dormancy. Every
  schedule uses its plain `interval_days` all year. Per-plant settings are kept, just not
  applied.

The toggle sits next to the editable winter-window dates (month/day, wrapping the new
year, with a "return to default" of Nov 1 to Mar 1) in app settings.

## Why

Winter intervals and dormancy are per schedule. Users in non-seasonal climates, or users
who do not want seasonal logic, had no way to switch the behavior off as a whole. "Off
ignores both" is the intuitive reading of a single switch: someone turning it off expects
every day to be the same, not a half-state.

## How it composes

`compute_due` takes an additive `seasonal_aware: bool` parameter. A settings-backed
provider supplies the window and the flag, read once per query so the query count stays
bounded. Because the default is on, behavior is unchanged until a user opts out.

A per-plant feeding mode is a different axis (per plant, not global) and is not covered
by this decision.
