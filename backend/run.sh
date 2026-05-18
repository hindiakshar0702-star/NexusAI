#!/bin/bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"

# Navigate to project root
cd "$PROJECT_ROOT"

# Load environment variables from .env file
set -a
source .env
set +a

# Start uvicorn with detected host and port
exec python -m uvicorn nexusai.api.app:app \
  --host "${BACKEND_HOST:-[IP_ADDRESS]}" \
  --port "${BACKEND_PORT:-8000}" \
  --reload
