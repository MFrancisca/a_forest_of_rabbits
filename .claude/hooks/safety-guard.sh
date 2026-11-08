#!/usr/bin/env bash
# PreToolUse safety guard.
#  - Bash: ask before commands that touch production or wipe a database.
#  - Edit/Write: deny edits to real secrets files (.env, .env.railway); .env.example is fine.
input=$(cat)
tool=$(jq -r '.tool_name // empty' <<<"$input")

decide() { # $1 = allow|ask|deny, $2 = reason
  jq -n --arg d "$1" --arg r "$2" \
    '{hookSpecificOutput:{hookEventName:"PreToolUse",permissionDecision:$d,permissionDecisionReason:$r}}'
  exit 0
}

case "$tool" in
  Bash)
    cmd=$(jq -r '.tool_input.command // empty' <<<"$input")
    if grep -qE 'railway[[:space:]].*(--environment|-e)[[:space:]=]+production' <<<"$cmd"; then
      decide ask "Command targets the Railway PRODUCTION environment."
    fi
    if grep -qE 'sync_staging_to_production' <<<"$cmd"; then
      decide ask "sync_staging_to_production overwrites production content (see docs/promote-staging-to-production.md)."
    fi
    if grep -qE '(manage\.py|django-admin)[[:space:]].*\bflush\b' <<<"$cmd"; then
      decide ask "manage.py flush empties every table, including Wagtail bootstrap rows."
    fi
    ;;
  Edit|Write|MultiEdit)
    path=$(jq -r '.tool_input.file_path // empty' <<<"$input")
    base=$(basename -- "$path")
    if [[ "$base" == ".env" || "$base" == ".env.railway" ]]; then
      decide deny "$base holds real credentials; edit it by hand (or update .env.example instead)."
    fi
    ;;
esac
exit 0
