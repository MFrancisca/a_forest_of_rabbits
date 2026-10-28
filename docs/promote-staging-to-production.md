# Promoting staging content to production

A one-time (or occasional, deliberate) procedure: wipe production's database
clean, then load staging's content into it. This is irreversible — rehearse
it against a disposable database before ever running it against the real
production environment.

It assumes the [staging environment](staging-environment.md) already
exists and holds the content you want to promote.

## Why this isn't just `flush` + `loaddata`

`manage.py flush` empties *every* table, including Wagtail's own bootstrap
rows — the root `Page`, the default `Locale`, and the root `Collection`.
None of these are recreated automatically by a flush (confirmed by testing
against a real database): Wagtail's initial-data migration that normally
creates them only runs once, the first time migrations are applied, not
again on a later flush. Without them, nothing else can be created — Wagtail
pages require a default `Locale` to save at all, and `sync_staging_to_production`
(the command used in step 4 below) needs a root `Page`/`Collection` to exist
so staging's content can be loaded in without colliding with them.

## Procedure

### 1. Capture the current default `Site`

For reference, in case you need to recreate it with the same hostname/port:

```
railway run --environment production python manage.py shell -c "
from wagtail.models import Site
print(list(Site.objects.filter(is_default_site=True).values()))
"
```

### 2. Flush production

```
railway run --environment production python manage.py flush
```

Run it *without* `--no-input` so Django's built-in confirmation prompt
(naming the target database) stays in place.

### 3. Recreate the bare bootstrap rows

```
railway run --environment production python manage.py shell -c "
from wagtail.models import Locale, Page, Collection
from wagtail.models.i18n import get_supported_content_language_variant
from django.conf import settings

code = get_supported_content_language_variant(settings.LANGUAGE_CODE)
Locale.objects.create(language_code=code)
Page.add_root(title='Root', slug='root')
Collection.add_root(name='Root')
"
```

Use Wagtail/treebeard's own tree API (`add_root`) rather than hand-built
`path`/`depth` values — it keeps the materialized path correct.

### 4. Sync staging's content in

Find staging's **public** Postgres URL (Railway dashboard → staging's
Postgres plugin → Connect → "Public Network" connection string — the public
one, not the internal one, since this command needs to reach staging's
database from outside its own private network).

Dry run first and sanity-check the printed per-model counts against what you
expect staging to hold:

```
railway run --environment production python manage.py sync_staging_to_production \
    --staging-url "<staging's public DATABASE_PUBLIC_URL>" --dry-run
```

Then run it for real:

```
railway run --environment production python manage.py sync_staging_to_production \
    --staging-url "<staging's public DATABASE_PUBLIC_URL>"
```

It will print a confirmation prompt before loading — type `yes` to proceed.
See the command's docstring
(`core/management/commands/sync_staging_to_production.py`) for exactly what
it copies, what it deliberately leaves out, and how it keeps content type /
collection / locale references consistent between the two databases even
when their internal pks don't line up.

### 5. Recreate the default `Site`

The sync command loads pages (including the promoted `HomePage`) but
deliberately doesn't touch `Site` — recreate it pointed at the loaded
`HomePage`, using the hostname/port captured in step 1 (or production's
real domain and port 443 if this is the real cutover):

```
railway run --environment production python manage.py shell -c "
from wagtail.models import Site
from blog.models import HomePage
home = HomePage.objects.first()
Site.objects.create(hostname='<production hostname>', port=443, root_page=home, is_default_site=True)
"
```

### 6. Sanity pass

```
railway run --environment production python manage.py create_site_skeleton
```

With `HomePage` already loaded, this should report everything as "already
exists — skipping." If it tries to create anything, something upstream
didn't load as expected — stop and investigate before treating the
promotion as complete.

### 7. Verify

- `curl` the production domain and confirm pages render.
- Check `/pigments/` and at least one project page return `200`.
- Spot-check that images render (shared R2 bucket means no file-copy step
  was needed, but worth confirming).
