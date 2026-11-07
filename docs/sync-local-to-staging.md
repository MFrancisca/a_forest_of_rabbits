# One-time sync: local database → staging

Replaces staging's content with the content in your **local** Docker Compose
database: pages (Home, Projects, About, every ProjectPage), categories, the
whole `pigments` app, and image records. It reuses
`sync_staging_to_production`. That command copies from any `--source-url`
into whatever database `default` resolves to, so here the source is your local
DB and the target is staging.

Like the staging → production promotion, this **wipes staging first**. It's
the same procedure as [promote-staging-to-production.md](promote-staging-to-production.md),
pointed the other way. Staging's users, revisions and Site row are not
copied.

## 0. Before you start

- **The schemas must match.** Commit and push any pending migrations, then
  wait for staging's deploy to finish so staging has applied them. Locally,
  `docker compose exec web python manage.py migrate` too.
- **Don't push to `master` while you're doing this.** Every staging deploy
  runs `create_site_skeleton`. If one lands between the flush (step 2) and
  the sync (step 4), it creates a fresh HomePage that will collide with
  the loaded one.
- Get staging's **public** Postgres URL: Railway → `staging` → its own
  Postgres (the independent one, see [staging-environment.md](staging-environment.md))
  → Connect → *Public Network*. Export it in your shell so the commands below
  can use it:

  ```bash
  export STAGING_DB='postgresql://postgres:...@....proxy.rlwy.net:NNNNN/railway'
  ```

All commands run in a one-off local `web` container. `config.settings.dev`
uses `DATABASE_PUBLIC_URL` as `default` whenever it's set. So passing
`-e DATABASE_PUBLIC_URL="$STAGING_DB"` makes **staging** the target, and the
local DB stays reachable as `db:5432` on the Compose network.

```bash
alias on-staging='docker compose run --rm -e DATABASE_PUBLIC_URL="$STAGING_DB" web python manage.py'
```

## 1. Upload local image files to R2

Image *records* are copied by step 4, but the files themselves must already
be in the shared R2 bucket. Run step 2 of [upload_images_to_r2.md](upload_images_to_r2.md)
(it skips files already in the bucket). You don't need that doc's fixture or
loaddata steps.

## 2. Flush staging

```bash
on-staging flush
```

Keep the confirmation prompt. It names the database it's about to wipe, so
check it's staging's `*.rlwy.net` host and not `db`.

## 3. Recreate Wagtail's bootstrap rows on staging

```bash
on-staging shell -c "
from wagtail.models import Locale, Page, Collection
from wagtail.models.i18n import get_supported_content_language_variant
from django.conf import settings
Locale.objects.create(language_code=get_supported_content_language_variant(settings.LANGUAGE_CODE))
Page.add_root(title='Root', slug='root')
Collection.add_root(name='Root')
"
```

## 4. Sync local → staging

Dry run, then check the per-model counts against what you have locally:

```bash
on-staging sync_staging_to_production \
    --source-url postgres://postgres:postgres@db:5432/esperanza \
    --fixture-path /app/local_sync_fixture.json --dry-run
```

Then for real. The prompt shows source and target host/name, so check them
before typing `yes`:

```bash
on-staging sync_staging_to_production \
    --source-url postgres://postgres:postgres@db:5432/esperanza \
    --fixture-path /app/local_sync_fixture.json
```

## 5. Recreate staging's Site and an admin user

```bash
on-staging shell -c "
from wagtail.models import Site
from blog.models import HomePage
Site.objects.create(hostname='appealing-heart-staging.up.railway.app', port=443,
                    root_page=HomePage.objects.first(), is_default_site=True)
"
on-staging createsuperuser
```

## 6. Verify

```bash
on-staging create_site_skeleton   # expect only "already exists — skipping" lines
```

Then open <https://appealing-heart-staging.up.railway.app/> and check the
homepage, `/projects/`, a project page, `/pigments/`, and that images render.
Delete `local_sync_fixture.json` once you're happy with the result.
