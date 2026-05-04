---
gsd_state_version: 1.0
milestone: v1.0
milestone_name: milestone
status: Executing Phase 06
stopped_at: Completed 06-01-PLAN.md
last_updated: "2026-03-23T19:07:11.265Z"
progress:
  total_phases: 7
  completed_phases: 6
  total_plans: 26
  completed_plans: 23
---

# Project State

## Project Reference

See: .planning/PROJECT.md (updated 2026-03-06)

**Core value:** Visitors can easily explore and access historical pigment knowledge and craft tutorials; the owner can add new content in minutes without friction.
**Current focus:** Phase 06 — production-deploy

## Current Position

Phase: 06 (production-deploy) — EXECUTING
Plan: 1 of 4

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
| Phase 05-content-migration P01 | 5min | 2 tasks | 2 files |
| Phase 05-content-migration P02 | 1 session | 1 tasks | 3 files |
| Phase 05-content-migration P03 | owner-session | 1 tasks | 1 files |
| Phase 05.1-google-sites-scraper-and-importer P01 | 2min | 2 tasks | 4 files |
| Phase 05.1-google-sites-scraper-and-importer P02 | 1min | 1 tasks | 1 files |
| Phase 05.1-google-sites-scraper-and-importer P03 | 2min | 1 tasks | 1 files |
| Phase 05.1-google-sites-scraper-and-importer P04 | 30min | 2 tasks | 1 files |
| Phase 06-production-deploy P01 | 2min | 3 tasks | 7 files |

## Accumulated Context

### Roadmap Evolution

- Phase 5.1 inserted after Phase 5: Google Sites Scraper and Importer (URGENT) — manual migration approach too slow for content volume; automated scraper/importer replaces manual Wagtail admin entry

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
- [Phase 05-content-migration]: All images go inline in body RichTextField during migration — cover_image field left blank
- [Phase 05-content-migration]: Checklist must be 100% complete before Phase 6 DNS cutover is permitted
- [Phase Phase 05-content-migration]: Tailwind typography plugin enabled via CDN query string so .prose class styles h2/h3/p/ul inside RichTextField body
- [Phase Phase 05-content-migration]: Google Sites collapsible boxes replaced with H2/H3 headings during migration; INFRA-v2-02 logged for future StreamField collapsible block
- [Phase 05-content-migration]: Checklist 100% complete is the gate condition for Phase 6 DNS cutover — no automated bypass
- [Phase 05.1-google-sites-scraper-and-importer]: Do NOT add requests to requirements — Playwright handles fetching (CONTEXT.md approach overridden by research)
- [Phase 05.1-google-sites-scraper-and-importer]: Dockerfile Chromium install uses --with-deps for headless operation in python:3.12-slim (+~130MB image, required)
- [Phase 05.1-google-sites-scraper-and-importer]: 9 test stubs created (not 8 as task name said) — behavior spec and done criteria both specify 9 including test_update_about_page
- [Phase 05.1-google-sites-scraper-and-importer]: create_project_page signature follows test stub contract (title, slug, body_html) not RESEARCH.md command-level signature — tests define the unit interface
- [Phase 05.1-google-sites-scraper-and-importer]: update_about_page accepts raw HTML and calls extract_body_html internally — matches test expectation
- [Phase 05.1-google-sites-scraper-and-importer]: Playwright import deferred inside handle() body to avoid ModuleNotFoundError at test collection time
- [Phase 05.1-google-sites-scraper-and-importer]: create_project_page called with keyword args matching Plan 02 unit-tested signature (title, slug, body_html, category_name=) not RESEARCH.md positional signature
- [Phase 05.1-google-sites-scraper-and-importer]: Playwright fetch and Django ORM calls split into two phases to avoid async context conflict — fetch all HTML first, then write all pages in a separate sync block
- [Phase 06-production-deploy]: STORAGES dict used (not DEFAULT_FILE_STORAGE/STATICFILES_STORAGE) — both removed in Django 5.1; dj_database_url.config() replaces individual POSTGRES_* vars; SECURE_SSL_REDIRECT omitted to avoid Cloudflare proxy redirect loops

### Pending Todos

None yet.

### Blockers/Concerns

- Django 5.1 in migration_plan.md is EOL — must update to Django 5.2 before writing any code
- Tailwind version (v3 vs v4) undecided — must resolve before template work in Phase 1
- `dj-database-url` missing from requirements — add before Phase 6 production settings
- Formula UI design (per-brand comparison layout) not yet designed — needed before Phase 3 implementation

### Quick Tasks Completed

| # | Description | Date | Commit | Directory |
|---|-------------|------|--------|-----------|
| 260504-001 | Update upload_images_to_r2 to use CLOUDFARE_* env vars | 2026-05-04 | pending | [260504-001-update-upload-images-r2-env-vars](.planning/quick/260504-001-update-upload-images-r2-env-vars/) |

## Session Continuity

Last session: 2026-03-12T20:38:32.859Z
Stopped at: Completed 06-01-PLAN.md
Resume file: None
