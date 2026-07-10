# Tasks - plant-detail (US-4.3)

Single frontend lane, TDD (red recorded per TEST-014).

1. [x] Test-foundation authored by test-engineer (pre-implementation pass)
2. [x] `PlantAttributesCard` - tests red → green (omit-empty matrix, tags, cachepot)
3. [x] `PlantSchedulesCard` - tests red → green (next-due, overdue emphasis, paused
       reason, empty state)
4. [x] `PlantGallery` - tests red → green (cover, thumbnail strip, +N overflow,
       empty state, opens PhotoGalleryModal)
5. [x] `PlantDetailHeader` + action wiring - tests red → green (modals open,
       onMutated reload, delete navigates to /plants)
6. [x] Page integration - refetch-after-mutation, timeline refresh key, loading/error
       states; existing PlantDetailPage tests kept/superseded per foundation §7
7. [x] E2E: production-path acceptance pass (A-1..A-7 smoke via Playwright against the
       built SPA served by the backend; axe scan clean at 390/1280 + empty state)
8. [x] FE-012 production-path verification: phone-390 / tablet-820 / desktop-1280 /
       empty-390 screenshots committed; zero console errors
9. [x] Story-complete test-engineer re-audit (APPROVED-WITH-CAVEATS → caveats cleared
       by task 7/8 acceptance-lane evidence)
10. [x] Three-reviewer gate (code / scope / security) + consolidation (HIGH race +
        MEDIUM coverage gap + LOW a11y fixed and re-verified; scope AC6 blocker
        cleared by task 8)
11. [ ] DoD gate + PR merge (PR open, awaiting maintainer)
