#!/usr/bin/env bash
set -euo pipefail

cd "$(dirname "$0")/../.."
source .venv/bin/activate

uvicorn src.api.app:app --reload --port 8000 &
BE_PID=$!

cleanup() {
  kill "$BE_PID" >/dev/null 2>&1 || true
}
trap cleanup EXIT

exec streamlit run streamlit_app.py

