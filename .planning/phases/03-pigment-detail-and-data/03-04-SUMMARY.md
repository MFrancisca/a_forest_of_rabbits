---
phase: 03-pigment-detail-and-data
plan: "04"
subsystem: ui
tags: [alpine.js, django, htmx, lightbox, template, browser-verification]

# Dependency graph
requires:
  - phase: 03-02
    provides: complete pigment detail view and template with Alpine.js reactive tabs, legend, lightbox, and manuscript table
  - phase: 03-03
    provides: load_initial_pigments management command seeding 4 pigments with formulas and manuscript links

provides:
  - human-verified confirmation that all interactive detail page behaviors work correctly in a real browser
  - media file serving fix in dev (config/urls.py)
  - Alpine.js x-data scope fix on manuscript rows (x-data on tbody not tr)

affects:
  - 04-tutorials (any future phase adding interactive UI should follow Alpine.js x-data patterns established here)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Alpine.js x-data on tbody not tr — row-level x-data creates isolated scopes; expansion state must live on the container"
    - "Media serving in dev requires static(MEDIA_URL, ...) appended to urlpatterns in config/urls.py when DEBUG=True"
    - "Legend panel responsive layout: right side desktop / stacked below formula on mobile"

key-files:
  created: []
  modified:
    - config/urls.py
    - pigments/templates/pigments/pigment_detail.html

key-decisions:
  - "config/urls.py must include static(MEDIA_URL, ...) for images to serve in dev — discovered during browser verification"
  - "Alpine.js x-data for manuscript row expansion belongs on tbody, not individual tr elements — tr-level x-data broke sibling row isolation"

patterns-established:
  - "Browser verification plans: add real multi-brand test data before human-verify checkpoint so the reviewer can exercise all interactive paths"
  - "Bugs found during human verification are deviation Rule 1; fix, commit, and re-confirm before closing the plan"

requirements-completed:
  - PIGM-02
  - PIGM-03

# Metrics
duration: ~10min
completed: 2026-03-09
---

# Phase 3 Plan 04: Browser Verification Summary

**Interactive pigment detail page browser-verified: Alpine.js tabs, reactive legend, expandable manuscript rows, and mobile layout all confirmed working after fixing media file serving and Alpine x-data scope on manuscript rows**

## Performance

- **Duration:** ~10 min
- **Started:** 2026-03-09
- **Completed:** 2026-03-09
- **Tasks:** 2 (1 auto + 1 human-verify checkpoint)
- **Files modified:** 2

## Accomplishments

- All 6 browser verification checks passed (navigation, formula tabs, legend panel, mobile layout, manuscript table, back button)
- Fixed media file 404s in dev by adding `static(MEDIA_URL, ...)` to `config/urls.py`
- Fixed Alpine.js x-data scope bug — moved `x-data` from `<tr>` to `<tbody>` so manuscript row expansion works correctly
- All 18 existing view tests remain green after both fixes

## Task Commits

1. **Task 1: Seed database and start dev server** — operational, no file commits
2. **Task 2: Browser verification checkpoint** — `21b7ea5` (fix: serve media files in dev + fix Alpine x-data scope on manuscript rows)

**Plan metadata:** `0e088f0` (docs: complete browser verification plan)

## Files Created/Modified

- `config/urls.py` — Added `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` for dev media serving
- `pigments/templates/pigments/pigment_detail.html` — Moved `x-data` from `<tr>` to `<tbody>` on manuscript rows

## Decisions Made

- Media URL pattern must be appended to `urlpatterns` in `config/urls.py` when `DEBUG=True`; omitting it causes all MEDIA_ROOT-served images to 404 in development.
- Alpine.js `x-data` on a `<tr>` creates an isolated scope per row, preventing rows from toggling correctly; `x-data` belongs on `<tbody>` so all rows share a single Alpine component.

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Media files serving missing in development (images 404ing)**
- **Found during:** Task 2 (Browser verification checkpoint)
- **Issue:** `config/urls.py` lacked `static(MEDIA_URL, ...)` URL pattern, so any image stored in MEDIA_ROOT returned 404 in the dev server
- **Fix:** Added `from django.conf import settings`, `from django.conf.urls.static import static`, and appended `static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)` to `urlpatterns`
- **Files modified:** `config/urls.py`
- **Verification:** Images loaded correctly in browser after fix
- **Committed in:** `21b7ea5`

**2. [Rule 1 - Bug] Alpine.js x-data scope bug on manuscript rows (rows not expanding)**
- **Found during:** Task 2 (Browser verification checkpoint)
- **Issue:** `x-data` was placed on individual `<tr>` elements; each row had an isolated Alpine scope, so clicking a row did not toggle the notes expansion correctly
- **Fix:** Moved `x-data` to the parent `<tbody>` element so all manuscript rows share one Alpine component instance
- **Files modified:** `pigments/templates/pigments/pigment_detail.html`
- **Verification:** Manuscript rows with notes expanded on click; rows without notes remained non-clickable; all 18 view tests still green
- **Committed in:** `21b7ea5`

---

**Total deviations:** 2 auto-fixed (both Rule 1 — bugs)
**Impact on plan:** Both fixes required for correct interactive behavior. No scope creep.

## Issues Encountered

None beyond the two bugs documented above, which were found and fixed during the verification session.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- Phase 3 is fully closed. All pigment detail interactive behaviors verified in a real browser.
- Phase 4 (blog/tutorials) can begin; the pigment detail page is the reference implementation for Alpine.js patterns in this project.
- No blockers.

---
*Phase: 03-pigment-detail-and-data*
*Completed: 2026-03-09*
