# Roadmap: Una Nueva Esperanza

## Overview

Six phases take the project from an empty repo to a live site at www.unanuovasperanza.art, replacing the existing Google Sites presence. The pigment database — the novel, differentiating feature — is built first because it carries the most unknown complexity. Blog and editorial content follow because they are proven Wagtail boilerplate. Content migration and production hardening close the project once all features exist to receive them.

## Phases

**Phase Numbering:**
- Integer phases (1, 2, 3): Planned milestone work
- Decimal phases (2.1, 2.2): Urgent insertions (marked with INSERTED)

Decimal phases appear between their surrounding integers in numeric order.

- [x] **Phase 1: Foundation and Models** - Working local environment with all pigment models migrated and Wagtail admin operational (completed 2026-03-08)
- [x] **Phase 2: Pigment Filtering** - HTMX-powered filterable pigment list at /pigments/ with bookmarkable URLs (completed 2026-03-09)
- [x] **Phase 3: Pigment Detail and Data** - Pigment detail pages with formula system and color swatches; initial data populated (completed 2026-03-09)
- [x] **Phase 4: Editorial Content** - Blog index, article pages, and About page live in Wagtail (completed 2026-03-09)
- [x] **Phase 5: Content Migration** - Existing Google Sites articles and images imported into Wagtail (completed 2026-03-10)
- [ ] **Phase 6: Production Deploy** - Site live at www.unanuovasperanza.art on Railway with R2 media storage and Cloudflare DNS

## Phase Details

### Phase 1: Foundation and Models
**Goal**: Owner can manage pigment taxonomy through Wagtail admin on a working local development environment
**Depends on**: Nothing (first phase)
**Requirements**: INFRA-01, PIGM-04, TEST-01, TEST-02
**Success Criteria** (what must be TRUE):
  1. Running `docker compose up` starts a working site with database at localhost
  2. Wagtail admin is accessible at /cms/ and requires login
  3. Owner can create, edit, and delete pigment taxonomy entries (ColorFamily, PigmentFamily, Country, Manuscript) from the admin without touching code
  4. All pigment-related database migrations apply cleanly with no errors
  5. All models have factory_boy factories; pytest test suite runs green with no fixture usage
**Plans**: 4 plans

Plans:
- [ ] 01-01-PLAN.md — Project skeleton, settings, Docker Compose, requirements, pyproject.toml
- [ ] 01-02-PLAN.md — Pigment models (all 11) with Wagtail snippet registrations and migrations
- [ ] 01-03-PLAN.md — Core app base template, navigation, footer, static CSS
- [ ] 01-04-PLAN.md — factory_boy factories and pytest test suite (TDD)

### Phase 2: Pigment Filtering
**Goal**: Visitors can browse and filter the pigment list by any combination of the five filter dimensions, with results updating without a full page reload
**Depends on**: Phase 1
**Requirements**: PIGM-01, TEST-03, TEST-04
**Success Criteria** (what must be TRUE):
  1. Visiting /pigments/ shows all pigments with filter controls visible
  2. Selecting a color family, pigment family, manuscript, country, or time period filter updates the list without a full page reload
  3. The URL in the browser updates to reflect active filters, and sharing that URL produces the same filtered results
  4. Pressing the browser back button after filtering returns a correctly-rendered full page (not a partial HTML fragment)
  5. Tests cover filter edge cases (empty results, combined filters, M2M joins with .distinct()) and HTMX partial/full-page response logic; all pass green
**Plans**: 3 plans

Plans:
- [ ] 02-01-PLAN.md — Failing test stubs (RED) + scaffold: view stub, URL route, template stubs
- [ ] 02-02-PLAN.md — View implementation + templates (GREEN) — all 11 tests pass
- [ ] 02-03-PLAN.md — Browser verification: HTMX swaps, pills, back button, bookmarkable URLs

### Phase 3: Pigment Detail and Data
**Goal**: Visitors can view complete pigment information — including images, manuscript provenance, and modern paint formulas — and the database contains real initial data
**Depends on**: Phase 2
**Requirements**: PIGM-02, PIGM-03
**Success Criteria** (what must be TRUE):
  1. Clicking a pigment in the list opens a detail page with description, reference images, and manuscript provenance links
  2. The detail page shows at least one formula section with brand name, paint color name, color swatch (rendered via CSS background-color), and mix proportions
  3. Multiple brand recipes for the same pigment appear side-by-side or in a clear comparison layout
  4. At least one real pigment with a complete formula is visible in the running database
  5. Detail view and formula rendering have backend tests using factories; all pass green
**Plans**: 4 plans

Plans:
- [ ] 03-01-PLAN.md — Paint.abbreviation migration, Manuscript.date_display, TDD scaffold (RED): test stubs, stub view, URL route, template stub
- [ ] 03-02-PLAN.md — Full pigment_detail view + complete pigment_detail.html template (GREEN): Alpine.js tabs, legend, lightbox, provenance table
- [ ] 03-03-PLAN.md — load_initial_pigments management command: 4 real pigments with formulas and manuscript links
- [ ] 03-04-PLAN.md — Browser verification: Alpine.js tab switching, reactive legend, lightbox, mobile layout

### Phase 4: Editorial Content
**Goal**: Visitors can read craft tutorials and art research articles, and learn about the site and its author
**Depends on**: Phase 1
**Requirements**: EDIT-01, EDIT-02
**Success Criteria** (what must be TRUE):
  1. Visiting the articles index shows a list of published articles with title and excerpt
  2. Clicking an article opens the full article page with body text and images
  3. An About page is accessible from the main navigation describing the site and its author
  4. Owner can create and publish a new article from Wagtail admin without touching code
  5. Blog page types and URL routing have backend tests using factories; all pass green
**Plans**: 4 plans

Plans:
- [x] 04-01-PLAN.md — TDD scaffold (RED): wagtail-factories install, blog factories, 9 failing test stubs, pyproject.toml coverage update
- [x] 04-02-PLAN.md — Blog models + migration (GREEN skeleton): Category snippet, ProjectsIndexPage, ProjectPage, AboutPage
- [x] 04-03-PLAN.md — Templates + management command + nav update (GREEN full): all 9 tests pass
- [x] 04-04-PLAN.md — Browser verification: admin publishing flow, nav, responsive About layout

### Phase 5: Content Migration
**Goal**: All existing Google Sites content is accessible on the new Wagtail site, with images preserved
**Depends on**: Phase 4
**Requirements**: INFRA-03
**Success Criteria** (what must be TRUE):
  1. Every article from the current Google Sites is readable on the new site
  2. Images from migrated articles display correctly (not broken links pointing to Google Sites)
  3. No content that exists on the current Google Sites is missing from the new site
**Plans**: 3 plans

Plans:
- [ ] 05-01-PLAN.md — Create migration guide + checklist documents (automated)
- [ ] 05-02-PLAN.md — Owner performs content migration (human checkpoint)
- [ ] 05-03-PLAN.md — Side-by-side review and sign-off (human checkpoint)

### Phase 05.1: Google Sites Scraper and Importer (INSERTED)

**Goal:** All 11 Google Sites articles are automatically scraped and imported as published Wagtail pages using Playwright; image placeholders mark where manually-uploaded images should be inserted
**Requirements**: INFRA-03
**Depends on:** Phase 5
**Plans:** 4 plans

Plans:
- [ ] 05.1-01-PLAN.md — Dependencies (playwright, beautifulsoup4, lxml), Dockerfile Chromium install, command stub, 8 failing test stubs (Wave 0)
- [ ] 05.1-02-PLAN.md — Implement helper functions extract_title, extract_body_html, slug_from_url — all 8 tests GREEN (TDD)
- [ ] 05.1-03-PLAN.md — Implement management command handle() with SCRAPE_CONFIG and Playwright fetcher
- [ ] 05.1-04-PLAN.md — Rebuild Docker image, run scraper against live site, human verification of created pages

### Phase 6: Production Deploy
**Goal**: The site is live at www.unanuovasperanza.art, media files persist across deployments, and DNS has been cut over from Google Sites
**Depends on**: Phase 5
**Requirements**: INFRA-02, INFRA-04
**Success Criteria** (what must be TRUE):
  1. Visiting www.unanuovasperanza.art serves the new Wagtail site over HTTPS
  2. Images uploaded through Wagtail admin are still visible after a new Railway deployment (persisted on Cloudflare R2)
  3. The pigment list, at least one pigment detail page, and at least one article are accessible to an anonymous visitor on the production URL
  4. The old Google Sites URL redirects or is fully replaced (hot swap complete)
**Plans**: TBD

## Progress

**Execution Order:**
Phases execute in numeric order: 1 → 2 → 3 → 4 → 5 → 6
Note: Phase 4 depends only on Phase 1 (independent of Phases 2-3) and can be planned in parallel, but executes sequentially before Phase 5.

| Phase | Plans Complete | Status | Completed |
|-------|----------------|--------|-----------|
| 1. Foundation and Models | 4/4 | Complete    | 2026-03-08 |
| 2. Pigment Filtering | 1/3 | Complete    | 2026-03-09 |
| 3. Pigment Detail and Data | 4/4 | Complete    | 2026-03-09 |
| 4. Editorial Content | 4/4 | Complete    | 2026-03-10 |
| 5. Content Migration | 3/3 | Complete   | 2026-03-10 |
| 5.1. Google Sites Scraper | 0/4 | Not started | - |
| 6. Production Deploy | 0/? | Not started | - |
