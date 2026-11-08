# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What this is

"A Forest of Rabbits" (`www.aforestofrabbits.art`): a personal art/research site built on Django 6.1 + Wagtail 8.0. Two content areas: editorial pages (blog app, Wagtail page tree) and a filterable database of historical medieval-manuscript pigments (pigments app, plain Django views over Wagtail snippets). Planning/roadmap lives in `.planning/` (GSD workflow).

## Commands

Local dev runs in Docker Compose (`web` + `postgres:16`); tests run from the host venv against SQLite.

```bash
docker compose up                                   # dev server on :8000 (config.settings.dev via .env)
docker compose exec web python manage.py migrate
docker compose exec web python manage.py makemigrations <app>
docker compose build web                            # rebuild after dependency/Wagtail upgrades — stale images fail confusingly

.venv/bin/pytest                                    # full suite, enforces 80% coverage on pigments/core/blog
.venv/bin/pytest pigments/tests/test_views.py::test_pigment_list_returns_200 --no-cov   # single test
.venv/bin/pytest blog --no-cov                      # one app, skip the coverage gate

.venv/bin/tailwindcss -i core/css/input.css -o core/static/css/output.css --minify   # rebuild CSS after template class changes
```

- `pyproject.toml` passes `--ds=config.settings.test` in `addopts`, which deliberately overrides the `DJANGO_SETTINGS_MODULE=config.settings.dev` that the web container exports. Don't remove it, or tests will run against the dev Postgres and write factory images into the real `media/`.
- Test settings use in-memory SQLite and a temp `MEDIA_ROOT`, and run the **real migrations** (no `MIGRATION_MODULES` override), so data migrations are exercised by the suite.
- `core/static/css/output.css` is committed; rebuild and commit it when Tailwind classes change. Tailwind v4 standalone binary, no Node.
- No linter/formatter is configured.

## Workflow

- When the work on a branch is done, run a code review of the changes (`/code-review --fix`) before saying it's ready to commit. Fix the bugs it finds, re-run `.venv/bin/pytest`, and report what was fixed and what was left for a decision.
- Whenever a new migration is created, check whether that app's migrations can be consolidated, so the migration tree stays small. Stability comes before tree size, so consolidation always happens in **two separate PRs**:
  1. **Squash, keeping the originals.** Run `squashmigrations` in the `web` container, then `chown -R 1000:1000 <app>/migrations` there too (files the container creates are root-owned, and the host can't edit them). Keep the replaced files and the squash's `replaces` list. Any database, at any state, can deploy this. Don't re-squash a squash that still has `replaces`: finish its step 2 first.
  2. **Remove the originals.** Delete the replaced files and the `replaces` list only once **both** of these show the squash commit (or a later one) as a successful deploy: staging (auto-deploys from `master`) and production (deployed manually). Read this from Railway's deployment list: startup runs `migrate`, so a successful deploy means the migrations applied. Don't query the production database. If production hasn't deployed it yet, leave step 2 pending and say so.
  3. **Optimize what's left** (can go in the step-2 PR). Once a migration is plain (no `replaces`), remove any `RunPython` steps that no database needs anymore, then run `python manage.py optimizemigration <app> <migration>` in the `web` container and `chown` the result. Don't collapse operations by hand. The optimizer only works inside one migration and can't merge operations across a `RunPython`, which is why those steps must go first. It rewrites the whole file, so put back any header comment afterwards. `optimizemigration --check <app> <migration>` exits non-zero if anything is still left to optimize.
  - In every step: update any `dependencies` on deleted names. Keep `RunPython` data migrations that any database still needs, and mark ones that are no longer needed `elidable=True`. Delete or rewrite tests that load a removed migration by name (`importlib.import_module('<app>.migrations.<name>')`). Make sure `makemigrations --check` reports no changes and `.venv/bin/pytest` passes (the suite runs the real migrations).

## Settings & environments

`config/settings/{base,dev,test,production}.py`.
- **dev**: Postgres from `DATABASE_PUBLIC_URL` if set (e.g. under `railway run`), else `POSTGRES_*` vars → Compose `db`. Adds debug-toolbar.
- **production**: `DATABASE_URL`, media on Cloudflare R2 via `S3Boto3Storage` served from `media.aforestofrabbits.art`, static via WhiteNoise manifest storage. Cloudflare terminates TLS — **never set `SECURE_SSL_REDIRECT`** (redirect loop); `SECURE_PROXY_SSL_HEADER` handles it.
- Deploy: Railway builds `Dockerfile.prod` (collectstatic at build time with placeholder env vars; startup runs `migrate`, `create_site_skeleton`, then gunicorn). Healthcheck is `/robots.txt`. `staging` auto-deploys on push to `master`; `production` deploys manually.
- `.env` / `.env.railway` hold real credentials (a project hook blocks Claude from editing them); `.env.example` is the template.

## Architecture

**URL routing** (`config/urls.py`): `/pigments/` → pigments app views; `/cms/` → Wagtail admin; everything else → Wagtail page serving.

**blog** — Wagtail page tree: `HomePage` → `ProjectsIndexPage` / `AboutPage` / `ProjectPage`. `ProjectPage` has two StreamFields (`body`, `technical_info`) built from StructBlocks defined in `blog/models.py`; `Category` is a snippet. Content was imported from the old Google Sites via `scrape_google_sites` (uses Playwright; run locally only — the prod image has no browser). StreamField shape changes are done with data migrations/commands (e.g. `split_project_body_streamfield`, migration 0014) that have dedicated tests.

**pigments** — Reference data (`ColorFamily`, `PigmentFamily`, `Country`, `Brand`, `Paint`, `Manuscript`, `Source`) registered as Wagtail snippets via `@register_snippet` in `models.py`, edited in the admin. `Pigment` and `Formula` are `ClusterableModel`s with inline `Orderable` children (`FormulaPart`, `PigmentManuscript`, `PigmentImage`). The public list only shows pigments that have formulas, and filter options are trimmed to values that actually occur. `pigment_list` serves three cases off HTMX headers: normal GET → full page, `HX-Request` → `pigment_list_partial.html` fragment, history restore → full page. HTMX is loaded from unpkg in `core/templates/base.html`. Initial data: `load_initial_pigments` (from `pigments/data/`).

**core** — Shared `base.html`/nav/footer, Tailwind source, and ops commands:
- `sync_staging_to_production --source-url ...` copies content from any source DB into whatever `default` resolves to (used both for local→staging and staging→prod). **Wipes the target first** and needs Wagtail's bootstrap rows (root Page, default Locale, root Collection) to exist — `flush` alone deletes them. Follow `docs/promote-staging-to-production.md` / `docs/sync-local-to-staging.md` exactly; both are irreversible.
- `upload_images_to_r2` pushes local media to R2 (`docs/upload_images_to_r2.md`).
