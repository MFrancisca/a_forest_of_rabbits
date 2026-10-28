# Setting up the staging Railway environment

One-time setup for a `staging` Railway environment with its own Postgres
database, which becomes the environment that auto-deploys on every push to
`master`. Production stops auto-deploying and becomes a manual/on-command
deploy from this point on.

## 1. Create the environment

Railway dashboard → environment dropdown → **New Environment** → duplicate
from `production`. Duplicating carries over the web service's build config
(it already uses `Dockerfile.prod` per `railway.toml`) and the existing
variable *names*, which you then edit per step 3 below.

## 2. Provision an independent Postgres

**Gotcha confirmed in practice:** Railway's "duplicate from production" does
*not* give the new environment its own database. It creates a `Postgres`
service instance in `staging` that looks separate in the dashboard, but is
wired to the exact same data volume production's `Postgres` uses (same
volume ID — verifiable via `railway status --json`, comparing each
environment's `volumeInstances`). If you leave the duplicated service's
`DATABASE_URL` as-is, staging and production silently share one live
database. There is no warning for this in the UI.

Fix: inside the `staging` environment, add a genuinely new database —
**+ New** → Database → PostgreSQL. This provisions its own volume. Then
explicitly point staging's web service `DATABASE_URL` at *this* new
Postgres's connection string (as a live reference, e.g.
`${{Postgres-xxxx.DATABASE_URL}}`, using whatever name Railway assigned
it) — not at the duplicated `Postgres` entry.

Once confirmed, remove the duplicated `Postgres` entry from `staging` —
but do it from the dashboard, not blind via CLI, and watch for a volume
named `postgres-volume` that may then show as "orphaned" in staging's view.
It isn't actually orphaned: it's the same volume production still has
mounted (`serviceId` just shows empty from staging's side after you remove
staging's pointer to it). **Do not delete that volume** — deleting it
deletes production's actual database storage. This dangling reference is a
Railway-side artifact of the duplicate bug above; if it doesn't clear on its
own, raise it with Railway support rather than deleting it yourself.

## 3. Set staging's service variables

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` (same module as prod — it's fully env-driven) |
| `SECRET_KEY` | A freshly generated value: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. Never reuse production's. |
| `ALLOWED_HOSTS` | Staging's `*.up.railway.app` hostname (Settings → Networking → Public Networking, once the service exists) |
| `WAGTAILADMIN_BASE_URL` | `https://<staging-hostname>.up.railway.app` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_ENDPOINT_URL` | Copied verbatim from production — staging and production intentionally share one R2 bucket, so promoted content's image references keep working with no file-copy step. Note: deleting/replacing an image in staging's Wagtail admin affects the same file production uses. |
| `DATABASE_URL` | A live reference to the *new, independent* Postgres from step 2 (e.g. `${{Postgres-xxxx.DATABASE_URL}}`) — not the duplicated `Postgres` entry. See step 2's gotcha before trusting whatever this got set to by default. |

## 4. Flip auto-deploy (the step most likely to be missed)

A duplicated environment inherits production's Source settings as-is — this
step is what actually makes staging the default deploy target.

- **Staging** → web service → Settings → Source: branch `master`, **Auto
  Deploy: ON**.
- **Production** → web service → Settings → Source: branch `master`, **Auto
  Deploy: OFF**. From here, production only deploys via the dashboard's
  manual "Deploy" button, or `railway up --environment production` /
  `railway redeploy --environment production`. This is a deliberate change
  from today's behavior (production currently auto-deploys on every push).

This toggle is dashboard-only — confirmed against Railway's own docs and
the CLI's `environment edit --service-config` dot-path schema, neither
exposes it. Don't waste time guessing a CLI/API field for it.

## 5. Verify

1. Push a trivial commit to `master`.
2. Railway dashboard → activity log: confirm only `staging` fired a new
   deployment; production shows no new deployment until manually triggered.
3. `curl -I https://<staging-hostname>.up.railway.app/robots.txt` → expect
   `200` (same healthcheck path `railway.toml` already defines).
4. `railway logs --environment staging` → expect a normal `Operations to
   perform: Apply all migrations` run. If you instead see errors related to
   `DATABASE_PUBLIC_URL`/`POSTGRES_*`, `DJANGO_SETTINGS_MODULE` wasn't set for
   staging — `manage.py`'s default is `config.settings.dev`, which looks for
   those instead.
