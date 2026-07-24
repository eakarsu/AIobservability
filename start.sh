#!/usr/bin/env bash
set -euo pipefail
ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PYTHON_BIN="${PYTHON_BIN:-$(pyenv which python3 2>/dev/null || command -v python3)}"

load_env_file() {
  local key value
  while IFS='=' read -r key value; do
    key="${key#export }"
    [[ "$key" =~ ^[A-Za-z_][A-Za-z0-9_]*$ ]] || continue
    [ -z "${!key+x}" ] || continue
    value="${value%$'\r'}"
    if [[ "$value" == \"*\" && "$value" == *\" ]]; then
      value="${value:1:${#value}-2}"
    elif [[ "$value" == \'*\' && "$value" == *\' ]]; then
      value="${value:1:${#value}-2}"
    fi
    export "$key=$value"
  done < "$ROOT/.env"
}

if [[ ! -f "$ROOT/.env" ]]; then echo "Missing .env; copy .env.example and provide secrets." >&2; exit 1; fi
load_env_file
case "${1:-all}" in
  all)
    "$ROOT/start.sh" backend & backend_pid=$!
    "$ROOT/start.sh" dashboard & dashboard_pid=$!
    cleanup() {
      trap - EXIT INT TERM
      kill "$backend_pid" "$dashboard_pid" 2>/dev/null || true
      wait "$backend_pid" "$dashboard_pid" 2>/dev/null || true
    }
    trap cleanup EXIT INT TERM
    wait "$backend_pid" "$dashboard_pid"
    ;;
  backend)
    assigned_port="${BACKEND_PORT:-${PORT:?PORT or BACKEND_PORT is required}}"
    sync_url="${SYNC_DATABASE_URL:-${DATABASE_URL:?DATABASE_URL is required}}"
    export SYNC_DATABASE_URL="$sync_url"
    case "$sync_url" in
      postgresql://*) export DATABASE_URL="postgresql+asyncpg://${sync_url#postgresql://}" ;;
      postgres://*) export DATABASE_URL="postgresql+asyncpg://${sync_url#postgres://}" ;;
    esac
    export SECRET_KEY="${SECRET_KEY:-${JWT_SECRET:?SECRET_KEY or JWT_SECRET is required}}"
    cors_origins="${CORS_ORIGINS:-[\"http://${FRONTEND_HOST:-127.0.0.1}:${FRONTEND_PORT:?FRONTEND_PORT or CORS_ORIGINS is required}\"]}"
    # pydantic-settings decodes list-valued environment variables as JSON.
    # Accept the common single-origin form used by local launchers too.
    if [[ "$cors_origins" != \[* ]]; then
      cors_origins="[\"$cors_origins\"]"
    fi
    export CORS_ORIGINS="$cors_origins"
    cd "$ROOT/backend"
    exec "$PYTHON_BIN" -m uvicorn app.main:app --host "${BACKEND_HOST:-${HOST:-127.0.0.1}}" --port "$assigned_port"
    ;;
  dashboard)
    cd "$ROOT/dashboard"
    exec npm run dev -- --host "${FRONTEND_HOST:-127.0.0.1}" --port "${FRONTEND_PORT:?FRONTEND_PORT is required}"
    ;;
  *) echo "Usage: $0 [all|backend|dashboard]" >&2; exit 64 ;;
esac
