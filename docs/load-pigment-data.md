# Loading pigment data into local, staging or production

Use this to add pigment data from `pigments/data/*.json` to a database that
already has content. Unlike [promote-staging-to-production.md](promote-staging-to-production.md)
and [sync-local-to-staging.md](sync-local-to-staging.md), it **never wipes
anything**:

- `load_initial_pigments` only adds rows. It matches pigments and manuscripts
  by exact name and sources by title, and never changes a description, link or
  source that already exists. The one exception: it fills in a missing source
  on an existing link.
- All the files you give it load in **one transaction**, so if any of them
  fails, nothing is written.
- `--dry-run` does the whole load, prints what it would create, and rolls
  back.

## The short version

```bash
scripts/load-pigments.sh <local|staging|production> pigments/data/manuscript_pigments.json pigments/data/supplemental_manuscript_pigments.json
```

The script:

1. finds the environment's Postgres service on Railway and checks it has a
   public URL (local uses the Compose `web` container instead);
2. checks the target has every migration this checkout expects
   (`migrate --check`), so the code and the schema match;
3. runs a dry run and prints the target database and every pigment,
   manuscript, source, color family, pigment family, country, brand and paint
   it would create;
4. asks you to confirm: type the environment name for staging and production,
   `y` for local;
5. backs up staging or production with `pg_dump` to `backups/` (git-ignored),
   unless you pass `--no-backup`;
6. loads.

Pass files **in dependency order**: `supplemental_manuscript_pigments.json`
adds links to pigments defined in `manuscript_pigments.json`, so the two go
together and in that order. Including a file that is already loaded is
harmless, because it just reports `0` new rows.

## Before you start (staging and production)

- **Turn on the Postgres TCP proxy** for that environment: Railway →
  environment → its Postgres service → Settings → Networking → TCP Proxy. The
  script stops and says so if it's off. You can turn it off again afterwards.
- **Use the deployed code.** The script runs *this checkout* against the
  remote database, so check out the commit that environment runs (usually
  `master`). Step 2 only catches a database that is *behind* this checkout:
  it misses one that has migrations this checkout doesn't know about, and any
  difference in the loader itself.
- **Railway CLI logged in and linked** to the project (`railway status`), and
  the host venv installed (`.venv/bin/python`). The script uses
  `config.settings.dev`, which connects through `DATABASE_PUBLIC_URL`.
- If the script can't find the Postgres service (e.g. it was renamed), set it:
  `RAILWAY_DB_SERVICE=Postgres-3v0u scripts/load-pigments.sh staging ...`.

## Reading the dry run

Check these before confirming:

- **`Target database:`** should be the host you expect (a `*.proxy.rlwy.net`
  host for staging or production, `db:5432` for local).
- **New pigments and manuscripts** should be the ones you meant to add. A name
  you expected to *already exist* means it was renamed in the admin; loading
  would create a duplicate next to it. Either rename it back or fix the name in
  the JSON first.
- **New families, countries and brands** are usually typos: each one becomes a
  new filter option on the public list.
- **Warnings** flag names that differ only in case from an existing one, new
  pigments with no description (usually a sign that the file that defines
  them wasn't loaded first), and existing pigments or manuscripts whose
  family, country or dates in the file differ from the database (the database
  value is kept).

## Without the script

The command works anywhere `manage.py` does:

```bash
docker compose exec web python manage.py load_initial_pigments --dry-run --data-file a.json b.json
```

## Undoing a load

Delete the rows in the Wagtail admin, or restore the backup. Restoring
replaces the whole database with its state at backup time, so anything edited
since is lost:

```bash
pg_restore --clean --no-owner --dbname "<public url>" backups/<env>-<timestamp>.dump
```
