---
phase: 01-foundation-and-models
plan: "04"
subsystem: testing
tags: [factory_boy, pytest, pytest-django, django-db, coverage, tdd, sqlite]

# Dependency graph
requires:
  - phase: 01-02
    provides: "All 11 pigment models (ColorFamily, PigmentFamily, Country, Brand, Paint, Manuscript, Pigment, Formula, FormulaPart, PigmentManuscript, PigmentImage)"

provides:
  - "pigments/factories.py — 11 DjangoModelFactory classes, each callable with zero arguments"
  - "pigments/tests/test_models.py — 15 pytest test functions covering all models"
  - "pigments/tests/conftest.py — pytest fixtures using factories"
  - "blog/tests/ — empty scaffold for Phase 4"
  - "conftest.py — root pytest conftest"
  - "config/settings/test.py — SQLite in-memory test settings"
  - "95% coverage on pigments and core"

affects:
  - Phase 4 blog models (will add blog factories and tests)
  - Any future plan adding new models (follow factory_boy pattern)
  - CI/CD pipeline (pytest configured with coverage thresholds)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "factory_boy DjangoModelFactory with Sequence for unique fields"
    - "SubFactory for FK relationships — no required args at any level"
    - "@pytest.mark.django_db for database tests"
    - "config/settings/test.py with SQLite :memory: for offline test runs"
    - "TDD RED/GREEN commit workflow"

key-files:
  created:
    - pigments/factories.py
    - pigments/tests/conftest.py
    - blog/tests/__init__.py
    - blog/tests/conftest.py
    - conftest.py
    - config/settings/test.py
  modified:
    - pigments/tests/test_models.py
    - pyproject.toml

key-decisions:
  - "SQLite :memory: test settings added (config/settings/test.py) — PostgreSQL unavailable in dev without Docker; all tests pass with SQLite"
  - "DJANGO_SETTINGS_MODULE changed from config.settings.dev to config.settings.test in pyproject.toml"
  - "--cov=blog removed from addopts in Phase 1 — blog has no code yet; re-add in Phase 4 when blog models land"
  - "PigmentImageFactory.image=None — null=True on the field makes this valid; no Wagtail image fixture needed in Phase 1"

patterns-established:
  - "Factory pattern: DjangoModelFactory + Sequence for unique fields + SubFactory for FKs"
  - "Test pattern: @pytest.mark.django_db + direct factory call (no conftest fixtures in test body)"
  - "Coverage: pigments and core tracked; blog excluded until Phase 4"
  - "TDD workflow: write failing tests (RED commit), write factories (GREEN commit)"

requirements-completed: [TEST-01, TEST-02]

# Metrics
duration: 20min
completed: 2026-03-08
---

# Phase 01 Plan 04: Test Infrastructure Summary

**factory_boy factories for all 11 pigment models with TDD workflow — 15 pytest tests passing at 95% coverage using SQLite in-memory database**

## Performance

- **Duration:** ~20 min
- **Started:** 2026-03-08T22:00:00Z
- **Completed:** 2026-03-08T22:19:44Z
- **Tasks:** 2 (RED + GREEN)
- **Files modified:** 8

## Accomplishments

- All 11 pigment model factories built with zero-argument construction and SubFactory chains
- 15 pytest tests cover model creation, __str__, FK relationships, and sequence uniqueness
- 95% test coverage on pigments app (well above 80% threshold)
- SQLite in-memory test settings added so tests run without PostgreSQL/Docker
- TDD RED/GREEN discipline maintained: ImportError confirmed before factories written

## Task Commits

1. **Task 1: RED — Failing tests for all 11 pigment models** - `010c925` (test)
2. **Task 2: GREEN — Factories + all tests passing** - `90d604a` (feat)

**Plan metadata:** (docs commit follows)

_Note: TDD tasks have two commits — test (RED) then feat (GREEN)_

## Files Created/Modified

- `pigments/factories.py` — 11 DjangoModelFactory classes; ColorFamilyFactory, PigmentFamilyFactory, CountryFactory, BrandFactory, PaintFactory, ManuscriptFactory, PigmentFactory, FormulaFactory, FormulaPartFactory, PigmentManuscriptFactory, PigmentImageFactory
- `pigments/tests/test_models.py` — Replaced structural tests with 15 factory_boy @pytest.mark.django_db tests
- `pigments/tests/conftest.py` — Fixtures: color_family, pigment, formula (using factories)
- `blog/tests/__init__.py` — Empty scaffold for Phase 4
- `blog/tests/conftest.py` — Empty scaffold for Phase 4
- `conftest.py` — Root pytest conftest (minimal)
- `config/settings/test.py` — SQLite :memory: test settings (no postgres required)
- `pyproject.toml` — Changed settings to config.settings.test; removed --cov=blog from addopts

## Decisions Made

- Used `config/settings/test.py` with SQLite `:memory:` — Django/PostgreSQL not available without Docker; SQLite is valid for model and factory testing
- Changed `DJANGO_SETTINGS_MODULE` in pyproject.toml from `config.settings.dev` to `config.settings.test`
- Removed `--cov=blog` from addopts — blog app has zero code in Phase 1; including it dilutes overall coverage score without benefit. Re-add in Phase 4.
- `PigmentImageFactory.image = None` — field is `null=True, blank=True` so this is valid; avoids needing Wagtail media fixtures in Phase 1

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 3 - Blocking] Created config/settings/test.py with SQLite database**
- **Found during:** Task 1 (RED — test run verification)
- **Issue:** pyproject.toml pointed to `config.settings.dev` which uses PostgreSQL; PostgreSQL not available without Docker, causing connection errors on test run
- **Fix:** Created `config/settings/test.py` inheriting from base with `DATABASES['default'] = sqlite3 :memory:`; updated pyproject.toml to use it
- **Files modified:** `config/settings/test.py` (created), `pyproject.toml` (DJANGO_SETTINGS_MODULE changed)
- **Verification:** All 15 tests pass, 95% coverage; `pytest pigments/tests/ -x -q` exits 0
- **Committed in:** `010c925` (RED task commit)

---

**Total deviations:** 1 auto-fixed (1 blocking)
**Impact on plan:** Essential fix — tests cannot run without a working database backend. SQLite :memory: is the standard Django test approach when postgres is unavailable. No scope creep.

## Issues Encountered

- Existing `pigments/tests/test_models.py` from an earlier attempt used Django `TestCase` (not factory_boy) — replaced entirely with factory_boy `@pytest.mark.django_db` tests per plan requirements. The old tests were not yet committed as part of any completed plan task.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Test infrastructure complete; any new model added to pigments app should get a factory and tests
- Blog tests scaffold in place; Phase 4 will add `BlogPageFactory` and tests when blog models land
- Coverage enforcement at 80% is active; future plans must maintain this threshold
- SQLite test settings will work for all model-level tests in Phase 1; if Phase 2+ needs postgres-specific features, they can override `@pytest.mark.django_db(databases=['default'])` or configure test DB

---
*Phase: 01-foundation-and-models*
*Completed: 2026-03-08*

## Self-Check: PASSED

- pigments/factories.py: FOUND
- pigments/tests/test_models.py: FOUND
- pigments/tests/conftest.py: FOUND
- blog/tests/__init__.py: FOUND
- blog/tests/conftest.py: FOUND
- conftest.py: FOUND
- config/settings/test.py: FOUND
- 01-04-SUMMARY.md: FOUND
- Commit 010c925 (RED): FOUND
- Commit 90d604a (GREEN): FOUND
