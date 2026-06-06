---
description: Explore the design space for a problem without committing to a spec
---
Explore: $ARGUMENTS

1. Map the problem against the current architecture (`ARCH-002/004/005`) and contracts (`API-*`). Check for context-pollution signals (`ARCH-004`) the exploration might surface.
2. Produce 2-4 candidate approaches with trade-offs (impact on stack `ARCH-001`, boundaries, dual-engine portability `ARCH-011`, contracts - breaking changes trigger planning mode `API-004`).
3. Recommend one; capture a cross-cutting decision as a draft ADR (`ARCH-010`) if warranted.
4. **No spec, no implementation, no commitment** - output is exploration material for a later `/spec-propose`.
5. Log the exploration outcome + any draft ADR to a worklog if this attaches to an existing change (`TRACE-003`); otherwise note it where the next `/spec-propose` can pick it up.
