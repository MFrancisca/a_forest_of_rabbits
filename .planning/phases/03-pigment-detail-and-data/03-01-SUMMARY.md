---
phase: 03-pigment-detail-and-data
plan: 01
subsystem: database, testing
tags: [django, wagtail, factory-boy, migrations, tdd, management-commands]

# Dependency graph
requires:
  - phase: 01-foundation-and-models
    provides: Paint, Manuscript, Pigment models and factories
  - phase: 02-pigment-filtering
    provides: pigment_list view, URL routing pattern for pigments app

provides:
  - Paint.abbreviation CharField(max_length=10, blank=True) with migration applied
  - Manuscript.date_display property returning formatted date strings
  - PaintFactory with abbreviation Sequence (A-Z cycling)
  - Stub pigment_detail view responding to /pigments/<pk>/
  - URL route pigments:detail
  - Minimal pigment_detail.html stub template
  - Failing test stubs for detail view and management command (RED phase)
  - Django management command scaffold (load_initial_pigments stub)

affects:
  - 03-02 (GREEN phase — will implement full detail view and management command)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - TDD RED-GREEN cycle: model + migration first, then test stubs, then implementation in next plan
    - Stub view + stub template before writing tests prevents TemplateDoesNotExist masking assertion failures
    - Management command skeleton (pass handle) before writing command tests

key-files:
  created:
    - pigments/migrations/0002_paint_abbreviation.py
    - pigments/management/__init__.py
    - pigments/management/commands/__init__.py
    - pigments/management/commands/load_initial_pigments.py
    - pigments/templates/pigments/pigment_detail.html
    - pigments/tests/test_management_commands.py
  modified:
    - pigments/models.py
    - pigments/factories.py
    - pigments/tests/test_models.py
    - pigments/tests/test_views.py
    - pigments/views.py
    - pigments/urls.py

key-decisions:
  - "Stub view returns render() with minimal template rather than HttpResponse — avoids TemplateDoesNotExist masking test assertion failures"
  - "test_load_initial_pigments_idempotent passes trivially (0==0) in RED phase — acceptable, will verify meaningfully in GREEN"

patterns-established:
  - "Infrastructure before tests: create management __init__ files, stub command, stub view, stub template BEFORE writing test stubs"
  - "Minimal stub template shows only {{ pigment.name }} so name tests pass but description/manuscript/context tests fail RED"

requirements-completed: [PIGM-02, PIGM-03]

# Metrics
duration: 3min
completed: 2026-03-09
---

# Phase 3 Plan 01: Pigment Detail Foundation Summary

**Paint.abbreviation + Manuscript.date_display added with migration, stub pigment_detail view + URL route scaffolded, 9 new TDD RED tests collected with zero import errors**

## Performance

- **Duration:** 3 min
- **Started:** 2026-03-09T16:41:53Z
- **Completed:** 2026-03-09T16:44:27Z
- **Tasks:** 2
- **Files modified:** 10

## Accomplishments
- Paint.abbreviation CharField(max_length=10, blank=True) added and migration applied
- Manuscript.date_display property returns formatted strings (c.800-900 / c.800 / em-dash)
- PaintFactory updated with abbreviation Sequence (cycles A-Z)
- Stub pigment_detail view + pigments:detail URL route operational
- 9 new test stubs collected with zero import errors — correct RED state (4 fail for right reasons)

## Task Commits

Each task was committed atomically:

1. **Task 1: Add Paint.abbreviation, Manuscript.date_display, run migration, update PaintFactory** - `3f69cbf` (feat)
2. **Task 2: Write failing test stubs + stub view + URL route + template stub (RED)** - `5d605e9` (test)

## Files Created/Modified
- `pigments/models.py` - Added Paint.abbreviation field + panel, Manuscript.date_display property
- `pigments/migrations/0002_paint_abbreviation.py` - Database migration for abbreviation field
- `pigments/factories.py` - PaintFactory gains abbreviation Sequence
- `pigments/tests/test_models.py` - 5 new model tests (abbreviation, date_display) all green
- `pigments/tests/test_views.py` - 7 new detail view tests (3 pass, 4 fail RED correctly)
- `pigments/tests/test_management_commands.py` - 2 management command tests (1 fails RED)
- `pigments/views.py` - Stub pigment_detail view using get_object_or_404
- `pigments/urls.py` - Detail route path('<int:pk>/', ..., name='detail')
- `pigments/templates/pigments/pigment_detail.html` - Minimal stub (name only)
- `pigments/management/__init__.py` - Django command discovery
- `pigments/management/commands/__init__.py` - Django command discovery
- `pigments/management/commands/load_initial_pigments.py` - Stub command (pass handle)

## Decisions Made
- Stub view renders template (not bare HttpResponse) to prevent TemplateDoesNotExist errors from masking assertion failures in content tests
- test_load_initial_pigments_idempotent passes trivially (0==0) — acceptable RED behavior, plan 03-02 implementation will make it meaningful

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

None.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Plan 03-01 RED phase complete: all 9 new tests collected, infrastructure in place
- Plan 03-02 (GREEN phase): implement full pigment_detail view (description, manuscript links, formulas context), implement load_initial_pigments command loading 3+ pigments
- No blockers

---
*Phase: 03-pigment-detail-and-data*
*Completed: 2026-03-09*

## Self-Check: PASSED

All files and commits verified:
- pigments/migrations/0002_paint_abbreviation.py: FOUND
- pigments/management/commands/load_initial_pigments.py: FOUND
- pigments/templates/pigments/pigment_detail.html: FOUND
- pigments/tests/test_management_commands.py: FOUND
- .planning/phases/03-pigment-detail-and-data/03-01-SUMMARY.md: FOUND
- Commit 3f69cbf: FOUND
- Commit 5d605e9: FOUND
