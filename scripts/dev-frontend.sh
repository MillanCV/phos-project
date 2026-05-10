#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
FRONTEND_DIR="$ROOT_DIR/phos-portal"
FRONTEND_PORT="${PHOS_FRONTEND_PORT:-5173}"

if ! command -v npm >/dev/null 2>&1; then
  echo "[frontend] 'npm' is required but not found."
  exit 1
fi

if [[ ! -d "$FRONTEND_DIR" ]]; then
  echo "[frontend] Could not find phos-portal directory."
  exit 1
fi

cd "$FRONTEND_DIR"
if [[ ! -d "node_modules" ]]; then
  echo "[frontend] Installing dependencies..."
  npm install
fi

echo "[frontend] Starting on http://127.0.0.1:${FRONTEND_PORT}"
npm run dev -- --host 127.0.0.1 --port "$FRONTEND_PORT"
