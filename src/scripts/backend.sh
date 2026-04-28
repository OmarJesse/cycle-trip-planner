#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate
exec uvicorn src.api.app:app --reload --port 8000 --log-level info --access-log

