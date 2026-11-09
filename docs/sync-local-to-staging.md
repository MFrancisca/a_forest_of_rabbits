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

- **Rebuild the local image first: `docker compose build web`.** Every
  command below runs local code against staging. A stale image (e.g. still on
  Wagtail 7.3 after the 8.0 upgrade) fails in confusing ways: `flush` can't
  truncate tables it has no model for (`wagtailadmin_formstate`), and saving
  pages fails on search-index columns it doesn't know (`title_text`).
- **The schemas must match.** Commit and push any pending migrations, then
  wait for staging's deploy to finish so staging has applied them. Locally,
  `docker compose exec web python manage.py migrate` too. If that fails with
  `relation "..." already exists`, the local database predates the migration
  squashes (Nov 2026). `showmigrations` no longer lists the deleted
  originals, so check what it recorded with
  `docker compose exec web python manage.py shell -c "from django.db.migrations.recorder import MigrationRecorder as R; print(list(R.Migration.objects.filter(app__in=['blog', 'pigments']).order_by('app', 'name').values_list('app', 'name')))"`.
  If it had applied every old migration (blog through
  `0018_projects_index_columns`, whether recorded under the original names or
  as `0001_squashed_0017_image_block_alignment` plus 0018; pigments through
  `0005_formula_image`), mark
  the squashes as applied once, then `migrate` again:
  `docker compose exec web python manage.py migrate blog 0001_squashed_0018_projects_index_columns --fake`
  and `docker compose exec web python manage.py migrate pigments 0001_squashed_0005_formula_image --fake`.
  If it was further behind, faking would skip real schema changes. Don't
  recreate the database: it holds the content this runbook copies. Instead,
  with a clean working tree, replay the old chains by checking out each of
  these commits in order and running `migrate` at each one:
  1. `1bb0ef5`: last commit with every original migration for both apps,
     including the old data conversions. Applies whatever is missing and
     records the first blog squash.
  2. `151117c`: records the pigments squash.
  3. `9dfa4f9`: records the blog squash through 0017.
  4. `eab877e`: applies `0018_projects_index_columns` if missing and records
     the final blog squash (through 0018).

  Then check out your branch again and `migrate`.
- **Staging's Postgres needs public access.** Railway → staging → its
  Postgres → Settings → Networking → TCP Proxy. `railway connect` doesn't get
  around this: it uses the same proxy. You can turn the proxy off afterwards.
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
