---
phase: 05-content-migration
plan: 02
subsystem: content
tags: [wagtail, migration, rich-text, tailwind, typography]

# Dependency graph
requires:
  - phase: 05-01
    provides: migration guide (docs/migration-guide.md) and blank checklist (docs/migration-checklist.md)
  - phase: 04-editorial-content
    provides: ProjectPage model, /projects/ URL routing, Wagtail admin publishing flow
provides:
  - All Google Sites articles published in Wagtail at /projects/<slug>/ URLs
  - H2/H3 headings rendering correctly in rich text body (Tailwind typography plugin enabled)
  - Migration guide updated with collapsible box workaround (use H2/H3 instead)
affects:
  - 06-deployment (DNS cutover unblocked — all content is live on Wagtail)

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Tailwind CDN ?plugins=typography query parameter enables .prose typography plugin for rich text rendering"
    - "Google Sites collapsible boxes replaced with H2/H3 headings during migration (no collapsible StreamField block yet)"

key-files:
  created: []
  modified:
    - core/templates/base.html
    - docs/migration-guide.md
    - .planning/REQUIREMENTS.md

key-decisions:
  - "Tailwind typography plugin enabled via CDN URL query string (?plugins=typography) so .prose class styles h2/h3/p/ul inside RichTextField body — discovered and fixed during migration"
  - "Google Sites collapsible boxes have no direct Wagtail equivalent; workaround is H2/H3 section headings — documented in migration guide and a future requirement (INFRA-v2-02) logged for StreamField collapsible blocks"

patterns-established:
  - "Tailwind typography plugin must be included whenever RichTextField body content contains headings — absence causes headings to render as unstyled body text"

requirements-completed:
  - INFRA-03

# Metrics
duration: ~1 session (owner-performed migration)
completed: 2026-03-09
---

# Phase 05 Plan 02: Content Migration Summary

**All Google Sites project articles migrated into Wagtail at /projects/ URLs with Tailwind typography plugin fix enabling correct H2/H3 rendering in rich text.**

## Performance

- **Duration:** 1 owner session
- **Started:** 2026-03-09
- **Completed:** 2026-03-09
- **Tasks:** 1 (human-performed migration)
- **Files modified:** 3 (base.html, migration-guide.md, REQUIREMENTS.md)

## Accomplishments

- Owner migrated all Google Sites articles from Calligraphy & Illumination, Clothing, and Armor categories into Wagtail ProjectPage entries
- All project articles published and accessible at /projects/<slug>/ URLs; verified in browser with images displaying correctly
- Tailwind typography plugin enabled (CDN URL ?plugins=typography) — H2/H3 headings in rich text body now render with correct hierarchy styles
- Migration guide updated with collapsible box workaround: use H2/H3 section headings instead of Google Sites collapsible boxes
- Future requirement INFRA-v2-02 logged in REQUIREMENTS.md for native StreamField collapsible block once StreamField lands

## Task Commits

This plan contained one human-action checkpoint — no automated task commits. Bugs discovered during migration were fixed and committed separately:

- `610a698` — fix(05): enable Tailwind typography plugin for rich text heading styles
- `a0b0d0d` — docs(05): note collapsible section workaround + add INFRA-v2-02 requirement

## Files Created/Modified

- `core/templates/base.html` — Added ?plugins=typography to Tailwind CDN URL so rich text headings render correctly
- `docs/migration-guide.md` — Added note: replace collapsible boxes with H2/H3 headings
- `.planning/REQUIREMENTS.md` — Added INFRA-v2-02 future requirement for StreamField collapsible block

## Decisions Made

- Tailwind typography plugin was not previously loaded; enabling it via CDN query string was the minimal fix rather than switching to a local Tailwind build
- No collapsible StreamField block exists yet; H2/H3 is the correct workaround and is documented for the owner going forward

## Deviations from Plan

### Auto-fixed Issues

**1. [Rule 1 - Bug] Tailwind typography plugin not loaded — H2/H3 headings unstyled in rich text**
- **Found during:** Task 1 (content migration — owner discovered headings rendered as unstyled body text)
- **Issue:** base.html loaded Tailwind CDN without the typography plugin, so .prose class had no h2/h3 styles
- **Fix:** Added ?plugins=typography to CDN URL; verified headings render with correct hierarchy in browser
- **Files modified:** core/templates/base.html
- **Committed in:** 610a698

**2. [Rule 2 - Missing Critical] Migration guide lacked collapsible box workaround**
- **Found during:** Task 1 (owner encountered Google Sites collapsible boxes with no Wagtail equivalent)
- **Issue:** Guide had no instruction for this content type; owner needed guidance to proceed
- **Fix:** Added workaround note (use H2/H3 headings); logged future requirement INFRA-v2-02 in REQUIREMENTS.md
- **Files modified:** docs/migration-guide.md, .planning/REQUIREMENTS.md
- **Committed in:** a0b0d0d

---

**Total deviations:** 2 auto-fixed (1 bug, 1 missing critical documentation)
**Impact on plan:** Both fixes necessary for migration to complete correctly. No scope creep.

## Issues Encountered

- Tailwind typography plugin absence only became visible when H2/H3 headings appeared in real migrated content — no test coverage for rich text visual rendering. Fixed immediately during migration.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness

- All project article content is live on Wagtail at /projects/<slug>/ URLs
- Phase 6 DNS cutover is now unblocked — content migration requirement (INFRA-03) satisfied
- Outstanding future item: StreamField collapsible block (INFRA-v2-02) — deferred, not a blocker

---
*Phase: 05-content-migration*
*Completed: 2026-03-09*
