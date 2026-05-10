#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/phos-engine"
BACKEND_PORT="${PHOS_BACKEND_PORT:-8000}"
PHOS_CAMERA_MOCK="${PHOS_CAMERA_MOCK:-true}"

if ! command -v uv >/dev/null 2>&1; then
  echo "[backend] 'uv' is required but not found."
  exit 1
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[backend] Could not find phos-engine directory."
  exit 1
fi

echo "[backend] Starting on http://127.0.0.1:${BACKEND_PORT}"
cd "$BACKEND_DIR"
PHOS_CAMERA_MOCK="$PHOS_CAMERA_MOCK" uv run uvicorn main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT"
