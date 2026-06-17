# Worklog - BUG-009 care timeline portrait-photo crop

Per-fix trail (`TRACE-001`). Entries newest-first: `time · actor · action · artifact · ref`.

## Entries

- `15:28 · claude/OPUS · REVIEW GATE: code APPROVED (no CRITICAL/HIGH) / scope PASS (only timeline touched; gallery grid + cover thumbnail correctly untouched; no stray binaries). Code MEDIUM (event-inline photo path shared TimelinePhotoImage but was unasserted) addressed: added object-contain assertion to the F-5 inline-photo test (7 pass). Security: pure CSS className change, no logic/data/network surface -> trivially clear, no separate pass run · /review · QG-004`
- `15:24 · claude/OPUS · GREEN + evidence: TimelinePhotoImage object-cover -> object-contain so portrait photos show whole (letterboxed) within the max-h-64 cap. FE gate green: lint/typecheck/format clean, 237 vitest, e2e 18/18 incl. new timeline-photo screenshot spec. FE-012 screenshot confirms the portrait fixture renders uncropped (all 4 corner markers + top/bottom bands visible) · CareTimeline.tsx, bugs/BUG-009-timeline-photo-screenshots/ · TEST-009/FE-012`
- `15:22 · claude/OPUS · RED->GREEN (TEST-014): new CareTimeline test "renders timeline photos uncropped" failed against unfixed code with "expect(img).toHaveClass(\"object-contain\")" (img had object-cover; 1 failed / 6 passed); green after the className change (7 passed) · CareTimeline.test.tsx · PRIN-III`
- `15:20 · claude/OPUS · intake: filed BUG-009 from template (severity medium, evidence reproduced). Surfaced by maintainer from a live portrait upload (Anthurium Oma) - distinct surface from BUG-008 (gallery modal); the detail-page timeline is a separate component with the same crop class. Dedupe: related to BUG-008, not a duplicate · bugs/BUG-009-timeline-photo-portrait-crop.md · VIRIDARIUM-73`
