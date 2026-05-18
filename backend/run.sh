#!/usr/bin/env bash
# ============================================================
# NexusAI backend launcher (Linux / macOS).
#
# Behavior:
#   1. Switch to this script's directory (the backend package root)
#      so uvicorn can import `nexusai.api.app`.
#   2. Load environment variables from .env if it exists.
#   3. Start uvicorn with --reload, honoring BACKEND_HOST and
#      BACKEND_PORT overrides if set.
#
# Strict mode is on: any error or unset reference aborts.
# ============================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Load .env if present. Values already in the environment win
# unless the .env line uses `=` directly (in which case they
# overwrite, which matches what `set -a; source` does).
if [ -f .env ]; then
  set -a
  # shellcheck disable=SC1091
  source .env
  set +a
fi

exec python -m uvicorn nexusai.api.app:app \
  --host "${BACKEND_HOST:-0.0.0.0}" \
  --port "${BACKEND_PORT:-8000}" \
  --reload
