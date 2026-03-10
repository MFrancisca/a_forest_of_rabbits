---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: completed
stopped_at: Completed 04-editorial-content-04-PLAN.md
last_updated: "2026-03-10T00:44:45.437Z"
last_activity: 2026-03-09 — Phase 4 editorial content complete; all browser checks passed
progress:
  total_phases: 6
  completed_phases: 4
  total_plans: 15
  completed_plans: 15
  percent: 100
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-06)

**Core value:** Visitors can easily explore and access historical pigment knowledge and craft tutorials; the owner can add new content in minutes without friction.
**Current focus:** Phase 4 complete — Phase 5 next

## Current Position

Phase: 4 of 6 (Editorial Content) — COMPLETE
Plan: 4 of 4 in current phase
Status: Phase 4 complete; all plans executed
Last activity: 2026-03-09 — Phase 4 editorial content complete; all browser checks passed

Progress: [██████████] 100% (Phase 4 of 6 complete; all 15 plans done)

## Performance Metrics

**Velocity:**
- Total plans completed: 0
- Average duration: —
- Total execution time: —

**By Phase:**

| Phase | Plans | Total | Avg/Plan |
|-------|-------|-------|----------|
| - | - | - | - |

**Recent Trend:**
- Last 5 plans: —
- Trend: —

*Updated after each plan completion*
| Phase 01-foundation-and-models P01 | 2 | 2 tasks | 25 files |
| Phase 01-foundation-and-models P04 | 20min | 2 tasks | 8 files |
| Phase 02-pigment-filtering P01 | 2min | 1 tasks | 5 files |
| Phase 02-pigment-filtering P02 | 3 | 2 tasks | 3 files |
| Phase 02-pigment-filtering P03 | 15min | 2 tasks | 1 files |
| Phase 03-pigment-detail-and-data P01 | 3min | 2 tasks | 10 files |
| Phase 03-pigment-detail-and-data P02 | 5min | 2 tasks | 2 files |
| Phase 03-pigment-detail-and-data P03 | 5min | 1 tasks | 2 files |
| Phase 03-pigment-detail-and-data P04 | 10min | 2 tasks | 1 files |
| Phase 03-pigment-detail-and-data P04 | 10min | 2 tasks | 2 files |
| Phase 04-editorial-content P01 | 10min | 3 tasks | 8 files |
| Phase 04-editorial-content P02 | 5min | 2 tasks | 3 files |
| Phase 04-editorial-content P03 | 15min | 2 tasks | 10 files |
| Phase 04-editorial-content P04 | 10min | 2 tasks | 1 files |

## Accumulated Context

### Decisions

Decisions are logged in PROJECT.md Key Decisions table.
Recent decisions affecting current work:

- [Pre-work]: Use Django 5.2 LTS (not 5.1 which is EOL) — change before Session 1
- [Pre-work]: Wagtail version must be verified against Django 5.2 compatibility matrix at Session 1 start
- [Pre-work]: Tailwind v3 vs v4 decision must be made before writing any templates
- [Pre-work]: Add `dj-database-url` to requirements before Phase 6
- [Phase 01-01]: Used python-decouple individual postgres vars instead of dj-database-url (deferred to Phase 6)
- [Phase 01-01]: psycopg[binary] (psycopg3) selected — NOT psycopg2-binary
- [Phase 01-01]: django.contrib.admin excluded from INSTALLED_APPS — Wagtail admin at /cms/ replaces it
- [Phase 01-04]: SQLite :memory: test settings added (config/settings/test.py) — PostgreSQL unavailable without Docker; all 15 tests pass with SQLite
- [Phase 01-04]: DJANGO_SETTINGS_MODULE changed to config.settings.test in pyproject.toml for all pytest runs
- [Phase 01-04]: --cov=blog removed from addopts in Phase 1 — blog has no code yet; will re-add in Phase 4
- [Phase 02-pigment-filtering]: Stub view returns HttpResponse (not render) — causes context=None failures which is acceptable RED state
- [Phase 02-pigment-filtering]: Template stubs created before running tests so TemplateDoesNotExist does not mask assertion failures
- [Phase 02-pigment-filtering]: Use request.headers.get('HX-Request') not request.META — cleaner Django 2.2+ API
- [Phase 02-pigment-filtering]: Django template comments ({# #}) instead of HTML comments in partial — HTML comments do not prevent parser from finding {%...%} tags
- [Phase 02-pigment-filtering]: Active pills row moved inside HTMX swap target (pigment_list_partial.html) — pills placed outside the swap target were not updated on filter change
- [Phase 03-pigment-detail-and-data]: Stub view renders template (not HttpResponse) to prevent TemplateDoesNotExist masking test assertion failures
- [Phase 03-pigment-detail-and-data]: Infrastructure before tests: create management __init__ files, stub command, stub view, stub template BEFORE writing test stubs
- [Phase 03-pigment-detail-and-data]: Lightbox x-data on outer wrapper, formula tabs x-data on formula section — Alpine v3 nested x-data is intentional and correct
- [Phase 03-pigment-detail-and-data]: JSON data file at pigments/data/ (plain directory, no __init__.py); DEFAULT_DATA_FILE resolved via Path(__file__) for cwd-independence; FormulaPart and PigmentManuscript guarded with .exists() for idempotency
- [Phase 03-pigment-detail-and-data]: Williamsburg formula added to seed data (not Wagtail admin) for version-controlled multi-brand tab testing
- [Phase 03-pigment-detail-and-data]: config/urls.py must include static(MEDIA_URL, ...) for images to serve in dev — discovered during browser verification
- [Phase 03-pigment-detail-and-data]: Alpine.js x-data for manuscript row expansion belongs on tbody, not individual tr elements — tr-level x-data broke sibling row isolation
- [Phase 04-editorial-content]: Create stub models in blog/models.py before tests to allow clean collection without ImportError (following Phase 3 pattern)
- [Phase 04-editorial-content]: blog/migrations/0001_initial.py required for Category model to resolve InvalidBasesError during test DB setup
- [Phase 04-editorial-content]: wagtail-factories 4.4.0 with no version pin in requirements/dev.txt; wagtail_factories.PageFactory for page model factories
- [Phase 04-editorial-content]: Deleted stub 0001_initial.py (unapplied) and regenerated from real models — keeps migration history clean with single initial migration
- [Phase 04-editorial-content]: ProjectPageFactory and AboutPageFactory require body field defaults — RichTextField not blank causes ValidationError in Wagtail full_clean()
- [Phase 04-editorial-content]: blog/migrations/0001_initial.py is root-owned; created blog/migrations_test/ with wagtailcore 0094 dep and MIGRATION_MODULES override in test settings
- [Phase 04-editorial-content]: wagtail_site fixture must explicitly update root_page when default site pre-exists from Wagtail initial migration — get_or_create does not update existing records
- [Phase 04-editorial-content]: Management command create_site_skeleton uses add_child + save_revision().publish() for idempotent ProjectsIndexPage and AboutPage creation
- [Phase 04-editorial-content P04]: Browser verification passed all 5 checks — admin publishing flow, /projects/ list with category chips, article detail, /about/ two-column layout, nav on desktop + mobile

### Pending Todos

None yet.

### Blockers/Concerns

- Django 5.1 in migration_plan.md is EOL — must update to Django 5.2 before writing any code
- Tailwind version (v3 vs v4) undecided — must resolve before template work in Phase 1
- `dj-database-url` missing from requirements — add before Phase 6 production settings
- Formula UI design (per-brand comparison layout) not yet designed — needed before Phase 3 implementation

## Session Continuity

Last session: 2026-03-09T20:36:00.000Z
Stopped at: Completed 04-editorial-content-04-PLAN.md
Resume file: None
