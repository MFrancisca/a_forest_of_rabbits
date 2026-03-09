---
phase: 03-pigment-detail-and-data
plan: "03"
subsystem: database
tags: [django, management-commands, json, seed-data, idempotent]

# Dependency graph
requires:
  - phase: 03-01
    provides: pigment detail view, models (Pigment, Formula, FormulaPart, PigmentManuscript, etc.)
  - phase: 03-02
    provides: management command stub, pigments.template.json schema reference
provides:
  - pigments/data/initial_pigments.json — 4 mock pigments (Blue, White, Red, Green) for development
  - pigments/management/commands/load_initial_pigments.py — data-driven idempotent seed command
  - --data-file argument for loading real research data without code changes
affects:
  - Phase 04+ — seed data enables meaningful filter and detail page testing in later phases

# Tech tracking
tech-stack:
  added: []
  patterns:
    - "Data-driven seed command: command reads JSON, no data hardcoded in Python"
    - "Idempotent seed: get_or_create for all top-level objects; guard child objects with .exists() check"
    - "Path resolution: Path(__file__).resolve().parent.parent.parent / 'data' / 'initial_pigments.json'"

key-files:
  created:
    - pigments/data/initial_pigments.json
  modified:
    - pigments/management/commands/load_initial_pigments.py

key-decisions:
  - "JSON data file lives alongside command at pigments/data/ (plain directory, no __init__.py)"
  - "DEFAULT_DATA_FILE resolved via Path(__file__) — works regardless of cwd at invocation"
  - "Formula parts guarded with formula.parts.exists() — avoids duplicate FormulaPart rows on re-run"
  - "PigmentManuscript links guarded with pigment.manuscript_links.filter(manuscript=ms).exists()"

patterns-established:
  - "Seed pattern: always get_or_create at every level; never bulk_create without duplicate guard"
  - "Data separation: swap JSON file for real data without touching command code"

requirements-completed: [PIGM-03]

# Metrics
duration: 5min
completed: 2026-03-09
---

# Phase 3 Plan 03: Seed Data and Management Command Summary

**Data-driven idempotent management command loads 4 mock pigments (Blue, White, Red, Green) from pigments/data/initial_pigments.json using get_or_create throughout; owner swaps JSON file for real data without code changes**

## Performance

- **Duration:** 5 min
- **Started:** 2026-03-09T17:00:00Z
- **Completed:** 2026-03-09T17:05:00Z
- **Tasks:** 1
- **Files modified:** 2

## Accomplishments
- Created `pigments/data/initial_pigments.json` with 4 mock pigments spanning Blue, White, Red, Green color families
- Replaced stub command with full data-driven implementation reading from JSON via `Path(__file__)` resolution
- Command accepts `--data-file` argument enabling owner to load real research data without modifying code
- All `get_or_create` calls throughout; child objects (FormulaPart, PigmentManuscript) guarded with `.exists()` checks for full idempotency
- Both management command tests pass green; full suite 40 passed at 94% coverage (gate: 80%)

## Task Commits

Each task was committed atomically:

1. **Task 1: Create JSON data file and implement data-driven management command** - `c623a40` (feat)

**Plan metadata:** (docs commit pending)

## Files Created/Modified
- `pigments/data/initial_pigments.json` - 4 mock pigments (Ultramarine Blue, Lead White, Red Ochre, Verdigris) with formulas and manuscript links
- `pigments/management/commands/load_initial_pigments.py` - Full data-driven idempotent command replacing stub

## Decisions Made
- JSON data file lives at `pigments/data/` as a plain directory (no `__init__.py`) — it is data, not a Python package
- `DEFAULT_DATA_FILE` resolved via `Path(__file__).resolve().parent.parent.parent / 'data' / 'initial_pigments.json'` — works regardless of working directory at invocation
- Formula parts guarded with `formula.parts.exists()` before creating `FormulaPart` rows — prevents duplicates on re-run
- `PigmentManuscript` links guarded with `pigment.manuscript_links.filter(manuscript=manuscript).exists()` — same idempotency guarantee

## Deviations from Plan

None - plan executed exactly as written.

## Issues Encountered

`python manage.py load_initial_pigments` fails outside Docker (PostgreSQL unreachable via hostname `db`). This is expected — the project uses Docker Compose for its runtime database. Tests use SQLite in-memory via `config.settings.test` and pass correctly. This is a pre-existing infrastructure constraint, not a deviation.

## User Setup Required

None - no external service configuration required.

## Next Phase Readiness
- Seed data is in place; `load_initial_pigments` can be run inside Docker to populate the development database
- 4 pigments spanning Blue, White, Red, Green give the filter page meaningful test coverage
- Owner can swap `pigments/data/initial_pigments.json` with real researched data at any time
- No blockers for Phase 4

---
*Phase: 03-pigment-detail-and-data*
*Completed: 2026-03-09*
