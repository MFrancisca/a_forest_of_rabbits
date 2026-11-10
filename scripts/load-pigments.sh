#!/usr/bin/env bash
# Load pigment JSON data into local, staging or production, without wiping anything.
#
#   scripts/load-pigments.sh <local|staging|production> [--no-backup] <data-file>...
#
# Example:
#   scripts/load-pigments.sh staging \
#     pigments/data/manuscript_pigments.json \
#     pigments/data/supplemental_manuscript_pigments.json
#
# Steps: check the target's migrations match this code, dry-run and show what
# would be created, ask you to confirm, back up (staging and production), load.
# The loader only adds rows and loads every file in one transaction.
# See docs/load-pigment-data.md.
set -euo pipefail

usage() {
  sed -n '2,10p' "$0" | sed 's/^# \{0,1\}//'
  exit 2
}

[[ $# -ge 2 ]] || usage
env_name=$1; shift
backup=1
files=()
for arg in "$@"; do
  case $arg in
    --no-backup) backup=0 ;;
    -*) echo "Unknown option: $arg" >&2; usage ;;
    *) files+=("$arg") ;;
  esac
done
[[ ${#files[@]} -gt 0 ]] || usage

repo_root=$(cd "$(dirname "$0")/.." && pwd)
cd "$repo_root"
for f in "${files[@]}"; do
  [[ -f $f ]] || { echo "Data file not found: $f" >&2; exit 1; }
  [[ $f != /* ]] || { echo "Use a path relative to the repo root: $f" >&2; exit 1; }
done

case $env_name in
  local)
    # Inside the web container, so it uses the Compose database. The repo is
    # mounted at /app, so the same relative paths work there.
    manage() { docker compose exec -T web python manage.py "$@" </dev/null; }
    backup=0
    ;;
  staging|production)
    # This checkout's code and the host venv, with the variables of the
    # environment's Postgres service: only that service has
    # DATABASE_PUBLIC_URL, which config.settings.dev connects through.
    # --no-local stops Railway rewriting it to the local Compose database.
    # The Postgres service is found by name; set RAILWAY_DB_SERVICE to override.
    db_service=${RAILWAY_DB_SERVICE:-}
    if [[ -z $db_service ]]; then
      mapfile -t candidates < <(railway service list --environment "$env_name" </dev/null | grep -E '^Postgres' || true)
      if [[ ${#candidates[@]} -ne 1 ]]; then
        echo "Couldn't pick $env_name's Postgres service (found: ${candidates[*]:-none})." >&2
        echo "Set RAILWAY_DB_SERVICE to its name." >&2
        exit 1
      fi
      db_service=${candidates[0]}
    fi
    echo "==> Using Railway service '$db_service' in $env_name"
    on_railway() { railway run --no-local --environment "$env_name" --service "$db_service" -- "$@" </dev/null; }
    manage() { on_railway env DJANGO_SETTINGS_MODULE=config.settings.dev .venv/bin/python manage.py "$@"; }
    if ! on_railway sh -c 'test -n "${DATABASE_PUBLIC_URL:-}"'; then
      echo "'$db_service' in $env_name has no DATABASE_PUBLIC_URL: its public TCP proxy is off." >&2
      echo "Turn it on in Railway ($db_service → Settings → Networking → TCP Proxy), then re-run." >&2
      exit 1
    fi
    ;;
  *) echo "Environment must be local, staging or production, not '$env_name'." >&2; exit 2 ;;
esac

# migrate --check only catches a database that is behind this checkout, not
# one that is ahead of it: use the commit the environment runs.
echo "==> Checking that $env_name has every migration this code expects"
if ! manage migrate --check >/dev/null; then
  echo "$env_name has migrations this checkout expects but it hasn't applied." >&2
  echo "Deploy or migrate first, so the schema matches this code." >&2
  exit 1
fi

echo "==> Dry run against $env_name"
manage load_initial_pigments --dry-run --data-file "${files[@]}"

echo
if [[ $env_name == local ]]; then
  read -r -p "Load this into local? [y/N] " answer || answer=
  [[ $answer == [yY] ]] || { echo "Nothing loaded."; exit 0; }
else
  echo "Check the 'Target database' line and the lists above before going on."
  read -r -p "Type '$env_name' to load this into $env_name: " answer || answer=
  [[ $answer == "$env_name" ]] || { echo "Nothing loaded."; exit 0; }
fi

if [[ $backup == 1 ]]; then
  mkdir -p backups
  dump="backups/$env_name-$(date +%Y%m%d-%H%M%S).dump"
  echo "==> Backing up $env_name to $dump"
  if ! on_railway sh -c 'pg_dump --format=custom --no-owner --file "$1" "$DATABASE_PUBLIC_URL"' sh "$dump"; then
    rm -f "$dump"
    echo "Backup failed, so nothing was loaded. If pg_dump is older than the server," >&2
    echo "install a matching one, or re-run with --no-backup if you accept the risk." >&2
    exit 1
  fi
  echo "    Restore with: pg_restore --clean --no-owner --dbname \"<public url>\" $dump"
fi

echo "==> Loading into $env_name"
manage load_initial_pigments --data-file "${files[@]}"
