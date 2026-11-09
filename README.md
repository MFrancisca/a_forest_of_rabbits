# A Forest of Rabbits

Source for [www.aforestofrabbits.art](https://www.aforestofrabbits.art), a personal art and research site. It has two parts:

- **Projects**: editorial pages about art and craft projects, written and organized in the Wagtail CMS.
- **Pigments**: a database of historical medieval-manuscript pigments that you can filter by color family, pigment family, country, manuscript and more. It lists each pigment's formulas, sources and the modern paints that match it.

Built with Django 6.1, Wagtail 8.0, PostgreSQL, Tailwind CSS v4 and HTMX.

## Project layout

| Path | What's there |
| --- | --- |
| `blog/` | Wagtail page tree (`HomePage` → `ProjectsIndexPage` / `AboutPage` / `ProjectPage`), StreamField blocks, `Category` snippet |
| `pigments/` | Pigment models (registered as Wagtail snippets), the filterable list view, initial data in `pigments/data/` |
| `core/` | Shared templates (`base.html`, nav, footer), Tailwind source, ops commands |
| `config/` | URLs and settings (`config/settings/{base,dev,test,production}.py`) |
| `docs/` | Runbooks for staging, syncing content and uploading media |

URL routing: `/pigments/` → pigments views, `/cms/` → Wagtail admin, everything else → Wagtail pages.

## Local development

Requirements: Docker with Compose, and Python 3.12 for running tests on the host.

```bash
cp .env.example .env              # then fill in the values
docker compose up                 # dev server at http://localhost:8000
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
docker compose exec web python manage.py load_initial_pigments   # optional seed data
```

The admin is at http://localhost:8000/cms/.

After you change dependencies or upgrade Wagtail, rebuild the image with `docker compose build web`. A stale image fails in confusing ways.

### CSS

Tailwind v4 runs from the standalone binary, so you don't need Node. The compiled `core/static/css/output.css` is committed, so rebuild it and commit it whenever template classes change:

```bash
.venv/bin/tailwindcss -i core/css/input.css -o core/static/css/output.css --minify
```

## Tests

Tests run from a host virtualenv against in-memory SQLite. They apply the real migrations and require 80% coverage on `pigments`, `core` and `blog`.

```bash
python3.12 -m venv .venv
.venv/bin/pip install -r requirements/dev.txt

.venv/bin/pytest                                   # full suite with coverage gate
.venv/bin/pytest blog --no-cov                     # one app
.venv/bin/pytest pigments/tests/test_views.py::test_pigment_list_returns_200 --no-cov
```

`pyproject.toml` forces `--ds=config.settings.test`, so tests never touch the dev database or `media/`, even inside the container.

## Management commands

| Command | Purpose |
| --- | --- |
| `load_initial_pigments` | Load the starter pigment data from `pigments/data/` |
| `create_site_skeleton` | Create the base page tree (runs on every deploy) |
| `scrape_google_sites` | One-off import from the old Google Sites. Needs Playwright, so run it locally only |
| `split_project_body_streamfield` | Data fix for the `ProjectPage` StreamField split |
| `sync_staging_to_production --source-url ...` | Copy all content from one database into another. **Wipes the target first.** |
| `upload_images_to_r2` | Push local media to Cloudflare R2 |

## Deployment

The site runs on [Railway](https://railway.app) and builds from `Dockerfile.prod`:

- Static files are collected at build time and served by WhiteNoise.
- Media lives on Cloudflare R2 and is served from `media.aforestofrabbits.art`.
- On startup the container runs `migrate`, then `create_site_skeleton`, then gunicorn. The healthcheck is `/robots.txt`.
- **staging** auto-deploys on every push to `master`. **production** is deployed manually.

Production reads `SECRET_KEY`, `DATABASE_URL`, `ALLOWED_HOSTS`, `WAGTAILADMIN_BASE_URL` and the R2 credentials (`AWS_ACCESS_KEY_ID`, `AWS_SECRET_ACCESS_KEY`, `AWS_STORAGE_BUCKET_NAME`, `AWS_S3_ENDPOINT_URL`). Cloudflare terminates TLS, so leave `SECURE_SSL_REDIRECT` unset. Setting it causes a redirect loop.

Runbooks:

- [Staging environment](docs/staging-environment.md)
- [Sync local content to staging](docs/sync-local-to-staging.md)
- [Promote staging to production](docs/promote-staging-to-production.md)
- [Upload images to R2](docs/upload_images_to_r2.md)

Both sync runbooks overwrite the target database and can't be undone. Follow them step by step.
