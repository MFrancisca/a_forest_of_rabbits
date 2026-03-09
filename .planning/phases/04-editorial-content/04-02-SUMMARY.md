---
phase: 04-editorial-content
plan: 02
subsystem: database
tags: [wagtail, django, models, migration, blog, snippet, richtext]

# Dependency graph
requires:
  - phase: 04-editorial-content
    plan: 01
    provides: stub models, 9 RED test stubs, blog/factories.py with 4 factories, initial stub migration
  - phase: 01-foundation-and-models
    provides: pytest infrastructure, Django/Wagtail project setup, config/settings/test.py
provides:
  - blog/models.py with full Category snippet + 3 Wagtail page models
  - blog/migrations/0001_initial.py with real DB schema (Category, ProjectsIndexPage, ProjectPage, AboutPage)
  - All 4 blog factories produce valid model instances (body fields added)
  - 9 blog tests collect cleanly, 1 passes (test_category_str), 8 fail RED awaiting templates
affects:
  - 04-03 (templates and views — 8 RED tests waiting for templates to go GREEN)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - Wagtail 7 imports: wagtail.models.Page, wagtail.fields.RichTextField, wagtail.admin.panels.FieldPanel
    - "@register_snippet decorator for Category (non-page Django model)"
    - ProjectsIndexPage.get_context returns live children ordered by -date under 'projects' key
    - RichTextField with explicit features list for ProjectPage.body
    - ForeignKey to 'wagtailimages.Image' with related_name='+' for image fields
    - All FK image fields use on_delete=SET_NULL with null=True, blank=True

key-files:
  created:
    - blog/migrations/0001_initial.py
  modified:
    - blog/models.py
    - blog/factories.py

key-decisions:
  - "Deleted stub 0001_initial.py (unapplied) and regenerated from real models — avoids needing a 0002 migration on top of stub"
  - "ProjectPageFactory and AboutPageFactory required body field addition — RichTextField not blank requires factory value for model.full_clean() to pass"

patterns-established:
  - "Wagtail page factories require all non-blank RichTextField fields to have defaults or Sequences"
  - "Stub migration delete-and-regenerate: valid when stub is unapplied and new models have more fields"

requirements-completed: [EDIT-01, EDIT-02]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 4 Plan 02: Blog Models and Migration Summary

**Category snippet + 3 Wagtail page models fully implemented, migration generated and applied, 9 tests collect and 1 passes RED with category __str__ working**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T20:09:22Z
- **Completed:** 2026-03-09T20:14:00Z
- **Tasks:** 2
- **Files modified:** 3

## Accomplishments
- blog/models.py replaced with full implementation: Category snippet, ProjectsIndexPage (get_context with live ordering), ProjectPage (5 custom fields), AboutPage (2 custom fields)
- Stub migration deleted and replaced with real 0001_initial.py covering all fields (68 lines, wagtailimages dependency included)
- Migration applied cleanly; `python manage.py check` passes with no issues
- ProjectPageFactory and AboutPageFactory updated with required body fields so model.full_clean() passes
- pytest blog/tests/ collects 9 tests, 0 errors, 1 passes (test_category_str), 8 fail RED waiting for templates

## Task Commits

Each task was committed atomically:

1. **Task 1: Implement blog/models.py with all four models** - `ed23135` (feat)
2. **Task 2: Generate and apply initial blog migration** - `acc862c` (feat)

## Files Created/Modified
- `blog/models.py` - Full implementation: Category @register_snippet + 3 Wagtail page models with all fields
- `blog/migrations/0001_initial.py` - Real DB schema migration for all 4 models
- `blog/factories.py` - Added body field to ProjectPageFactory and AboutPageFactory

## Decisions Made
- Deleted the stub 0001_initial.py (which was unapplied) and regenerated from the real models rather than creating a 0002 migration. This keeps migration history clean with a single initial migration reflecting the real schema.
- Added body defaults to both page factories because RichTextField (no blank=True) causes ValidationError during Wagtail's page.full_clean() when factory creates without body.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 2 - Missing Critical] Added body field to ProjectPageFactory and AboutPageFactory**
- **Found during:** Task 2 (Generate and apply initial blog migration)
- **Issue:** Running pytest after migration showed ValidationError: `{'body': ['This field cannot be blank.']}` in ProjectPageFactory. Both ProjectPage.body and AboutPage.body are RichTextField (not blank), but the factories from 04-01 didn't include body defaults because the stub models had no fields at that time.
- **Fix:** Added `body = factory.Sequence(lambda n: f'<p>Body content for project {n}</p>')` to ProjectPageFactory and `body = '<p>About this site.</p>'` to AboutPageFactory
- **Files modified:** blog/factories.py
- **Verification:** pytest blog/tests/ collects 9 tests, 0 errors; test_category_str passes; remaining 8 fail RED with 404 (no templates, correct state)
- **Committed in:** acc862c (Task 2 commit)

---

**Total deviations:** 1 auto-fixed (missing critical factory field)
**Impact on plan:** Required for factories to produce valid page instances. No scope creep — body is part of the model spec from 04-CONTEXT.md.

## Issues Encountered
None beyond the factory body field deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 8 RED tests ready for Plan 04-03 to add templates (make GET /projects/, /projects/<slug>/, /about/ return 200)
- test_category_str already GREEN (1 of 9 passing)
- All model fields correctly defined and migrated; no schema changes expected in 04-03
- Factory infrastructure complete and validated against real model constraints

---
*Phase: 04-editorial-content*
*Completed: 2026-03-09*

## Self-Check: PASSED

- blog/models.py: FOUND
- blog/migrations/0001_initial.py: FOUND
- blog/factories.py: FOUND
- 04-02-SUMMARY.md: FOUND
- Commit ed23135: FOUND
- Commit acc862c: FOUND
