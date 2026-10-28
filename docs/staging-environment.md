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

If duplicating the environment didn't create a Postgres plugin scoped to
`staging`, add one explicitly: inside the `staging` environment, **+ New** →
Database → PostgreSQL.

Confirm staging's web service's `DATABASE_URL` variable is a Railway
reference (`${{Postgres.DATABASE_URL}}`) pointing at *this* staging Postgres
instance — never production's.

## 3. Set staging's service variables

| Variable | Value |
|---|---|
| `DJANGO_SETTINGS_MODULE` | `config.settings.production` (same module as prod — it's fully env-driven) |
| `SECRET_KEY` | A freshly generated value: `python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"`. Never reuse production's. |
| `ALLOWED_HOSTS` | Staging's `*.up.railway.app` hostname (Settings → Networking → Public Networking, once the service exists) |
| `WAGTAILADMIN_BASE_URL` | `https://<staging-hostname>.up.railway.app` |
| `AWS_ACCESS_KEY_ID` / `AWS_SECRET_ACCESS_KEY` / `AWS_STORAGE_BUCKET_NAME` / `AWS_S3_ENDPOINT_URL` | Copied verbatim from production — staging and production intentionally share one R2 bucket, so promoted content's image references keep working with no file-copy step. Note: deleting/replacing an image in staging's Wagtail admin affects the same file production uses. |
| `DATABASE_URL` | Leave as the Railway-injected reference to staging's own Postgres — do not hand-set. |

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
