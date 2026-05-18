#!/usr/bin/env bash
set -euo pipefail
cd "$(dirname "$0")"
exec python -m uvicorn nexusai.api.app:app --host 0.0.0.0 --port 8000 --reload
