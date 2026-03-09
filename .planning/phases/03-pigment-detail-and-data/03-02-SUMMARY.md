---
phase: 03-pigment-detail-and-data
plan: 02
subsystem: ui, database
tags: [django, wagtail, alpine.js, tailwind, templates, tdd]

# Dependency graph
requires:
  - phase: 03-pigment-detail-and-data
    plan: 01
    provides: Stub pigment_detail view, pigments:detail URL route, failing RED test stubs, Paint.abbreviation, Manuscript.date_display

provides:
  - Full pigment_detail view with select_related + prefetch_related optimized queryset
  - Complete pigment_detail.html template with Alpine.js formula tabs, legend panel, lightbox, provenance table
  - All 9 detail view tests GREEN (18 total test_views.py tests pass)

affects:
  - 03-03 (management command implementation — test_load_initial_pigments RED test still pending)
  - 03-04 (visual verification of Alpine.js tabs and lightbox)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wagtail image renditions via {% image obj fill-WxH as rendition %} — never inline in src="" attribute
    - Alpine.js nested x-data components: outer lightbox scope, inner formula tab scope
    - x-cloak style in extra_head block prevents FOUC before Alpine initializes
    - Mobile-first legend: inline inside tab panel with lg:hidden, separate sticky panel with hidden lg:block
    - class attribute merging: static classes first, conditional appended via template if tag (no duplicate class attrs)

key-files:
  created: []
  modified:
    - pigments/views.py
    - pigments/templates/pigments/pigment_detail.html

key-decisions:
  - "Lightbox x-data on outer wrapper div; formula tabs x-data on formula section div — Alpine v3 nested x-data is intentional and correct"
  - "class attribute on manuscript <tr> merged: static border class first, cursor/hover conditionally appended — avoids duplicate class attributes"

patterns-established:
  - "Full context dict key names must match template variable names exactly — documented in plan interfaces block"
  - "Pre-existing RED management command test is out of scope for detail view GREEN phase"

requirements-completed: [PIGM-02, PIGM-03]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 3 Plan 02: Pigment Detail View GREEN Phase Summary

**Full pigment_detail view with optimized queryset + complete Alpine.js detail template with formula tabs, legend panel, lightbox, and manuscript provenance table — all 18 view tests green**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T16:46:47Z
- **Completed:** 2026-03-09T16:52:00Z
- **Tasks:** 2
- **Files modified:** 2

## Accomplishments
- pigment_detail view replaced with full implementation: select_related('brand'), prefetch_related('parts__paint'), featured_image/additional_images split, manuscript_links with select_related('manuscript__country')
- Complete pigment_detail.html template: h1 + family tags, description block, featured image with lightbox, formula section with Alpine.js brand tabs and dual legend (desktop sidebar + mobile inline), additional images strip, manuscript provenance table
- All 18 test_views.py tests pass green (9 list view + 9 detail view)
- Coverage 93.70% — well above 80% gate

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement full pigment_detail view** - `bc20bc8` (feat)
2. **Task 2: Implement complete pigment_detail.html template** - `3e6617a` (feat)

## Files Created/Modified
- `pigments/views.py` - Full pigment_detail view replacing stub; formulas/images/manuscript_links querysets
- `pigments/templates/pigments/pigment_detail.html` - Complete detail template with Alpine.js tabs, lightbox, provenance table

## Decisions Made
- Lightbox x-data on outer wrapper and formula tabs x-data on the formula section div are separate nested Alpine components — Alpine v3 handles nested x-data correctly, no conflicts
- Merged duplicate class attributes on manuscript `<tr>` tags by appending conditional classes to a single class attribute (static base + conditional suffix)

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

Pre-existing failure: `test_load_initial_pigments_creates_pigments` was intentionally RED from plan 03-01 (stub management command). Out of scope for this plan — will be addressed in plan 03-03.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Detail view fully implemented and all 18 view tests pass green
- Alpine.js tabs and lightbox markup in place — ready for visual verification in plan 03-04
- plan 03-03 (load_initial_pigments command) is the remaining RED test to turn GREEN
- No blockers

---
*Phase: 03-pigment-detail-and-data*
*Completed: 2026-03-09*

## Self-Check: PASSED

All files and commits verified:
- pigments/views.py: FOUND
- pigments/templates/pigments/pigment_detail.html: FOUND
- .planning/phases/03-pigment-detail-and-data/03-02-SUMMARY.md: FOUND
- Commit bc20bc8: FOUND
- Commit 3e6617a: FOUND
