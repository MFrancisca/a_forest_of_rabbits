---
phase: 04-editorial-content
plan: 01
subsystem: testing
tags: [wagtail-factories, factory-boy, pytest, blog, wagtail, tdd]

# Dependency graph
requires:
  - phase: 01-foundation-and-models
    provides: pytest infrastructure, factory-boy, pyproject.toml test config, blog app placeholder
provides:
  - wagtail-factories 4.4.0 installed and importable
  - blog/factories.py with CategoryFactory, ProjectsIndexPageFactory, ProjectPageFactory, AboutPageFactory
  - blog/tests/conftest.py with 5 fixtures for Wagtail page tree setup
  - blog/tests/test_models.py with 9 RED failing test stubs
  - blog/migrations/0001_initial.py for stub models
  - --cov=blog added to pytest coverage config
affects:
  - 04-02 (implements models to make RED tests go GREEN)
  - 04-03 (templates and views)

# Tech tracking
tech-stack:
  added: [wagtail-factories==4.4.0]
  patterns:
    - wagtail_factories.PageFactory as base for Wagtail page model factories
    - Stub models in blog/models.py allow test collection before full model implementation
    - conftest.py builds Wagtail page tree (root_page -> projects_index/about_page -> project pages)

key-files:
  created:
    - blog/factories.py
    - blog/tests/test_models.py
    - blog/migrations/0001_initial.py
    - blog/migrations/__init__.py
  modified:
    - blog/models.py
    - blog/tests/conftest.py
    - requirements/dev.txt
    - pyproject.toml

key-decisions:
  - "Create stub models in blog/models.py before tests to allow clean collection without ImportError (following Phase 3 pattern)"
  - "blog/migrations/0001_initial.py required for Category model (non-page Django model) to resolve InvalidBasesError during test DB setup"
  - "wagtail-factories 4.4.0 used with no version pin in requirements/dev.txt"

patterns-established:
  - "Wagtail page factory pattern: wagtail_factories.PageFactory + slug Sequence + parent kwarg in fixture"
  - "conftest.py page tree: root_page (depth=1) -> wagtail_site -> index pages -> child pages"
  - "Category (snippet) uses DjangoModelFactory; page models use wagtail_factories.PageFactory"

requirements-completed: [EDIT-01, EDIT-02]

# Metrics
duration: 10min
completed: 2026-03-09
---

# Phase 4 Plan 01: Editorial Content TDD Scaffold Summary

**wagtail-factories 4.4.0 installed, 4 blog factories created, 9 RED test stubs written covering all EDIT-01 and EDIT-02 behaviors with clean collection**

## Performance

- **Duration:** 10 min
- **Started:** 2026-03-09T20:05:21Z
- **Completed:** 2026-03-09T20:15:00Z
- **Tasks:** 3
- **Files modified:** 8

## Accomplishments
- wagtail-factories 4.4.0 installed in Docker container and added to requirements/dev.txt
- 4 factories created (CategoryFactory, ProjectsIndexPageFactory, ProjectPageFactory, AboutPageFactory) using established wagtail_factories.PageFactory pattern
- 9 RED test stubs written covering: category __str__, index live-only display, index ordering, empty state, project detail render, URL routing for /projects/ and /projects/<slug>/, /about/ render and URL
- blog coverage tracking re-enabled in pyproject.toml (--cov=blog, source = blog)
- Stub models and initial migration created to allow clean pytest collection

## Task Commits

Each task was committed atomically:

1. **Task 1: Install wagtail-factories and update coverage config** - `be14ad2` (chore)
2. **Task 2: Create blog/factories.py with all four factories** - `5b7de1d` (feat)
3. **Task 3: Write conftest fixtures and 9 RED test stubs** - `3e1de5b` (test)

## Files Created/Modified
- `requirements/dev.txt` - Added wagtail-factories dependency
- `pyproject.toml` - Added --cov=blog to addopts; added blog to coverage source list
- `blog/factories.py` - CategoryFactory, ProjectsIndexPageFactory, ProjectPageFactory, AboutPageFactory
- `blog/models.py` - Stub models: Category, ProjectsIndexPage, ProjectPage, AboutPage
- `blog/migrations/0001_initial.py` - Initial migration for stub models
- `blog/migrations/__init__.py` - Migration package init
- `blog/tests/conftest.py` - 5 fixtures: root_page, wagtail_site, projects_index, about_page, published_project
- `blog/tests/test_models.py` - 9 RED test stubs

## Decisions Made
- Created stub models in blog/models.py before writing tests (following Phase 3 pattern: infrastructure before tests, stubs before assertions) so pytest collects cleanly without ImportError
- Had to create blog/migrations/0001_initial.py because Category (a plain Django model, not a Wagtail Page) requires a migration for pytest to set up the test database; without it, pytest raised `InvalidBasesError` on test collection
- No version pin on wagtail-factories in requirements/dev.txt (latest 4.4.0 supports Wagtail 7 as specified in plan)

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created blog/migrations/0001_initial.py**
- **Found during:** Task 3 (Write conftest fixtures and 9 RED test stubs)
- **Issue:** Running pytest raised `django.db.migrations.exc.InvalidBasesError` because blog app has no migrations; Category (plain Django model) requires a migration for test DB setup
- **Fix:** Ran `docker compose exec web python manage.py makemigrations blog` to generate initial migration for all 4 stub models
- **Files modified:** blog/migrations/0001_initial.py, blog/migrations/__init__.py
- **Verification:** pytest blog/tests/ --collect-only shows 9 tests collected with zero import errors
- **Committed in:** 3e1de5b (Task 3 commit)

---

**Total deviations:** 1 auto-fixed (blocking issue)
**Impact on plan:** Migration is required infrastructure for test DB setup. No scope creep.

## Issues Encountered
None beyond the migration deviation above.

## User Setup Required
None - no external service configuration required.

## Next Phase Readiness
- 9 RED tests ready for Plan 04-02 to implement models (make tests go GREEN)
- Factory infrastructure complete: CategoryFactory, ProjectsIndexPageFactory, ProjectPageFactory, AboutPageFactory
- conftest.py page tree fixtures established for Wagtail routing tests
- All blog coverage tracking configured

---
*Phase: 04-editorial-content*
*Completed: 2026-03-09*
