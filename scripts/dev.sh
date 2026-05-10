#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

echo "[dev] Use two terminals:"
echo
echo "  Terminal 1 (backend):"
echo "    cd \"$ROOT_DIR\" && bash scripts/dev-backend.sh"
echo
echo "  Terminal 2 (frontend):"
echo "    cd \"$ROOT_DIR\" && bash scripts/dev-frontend.sh"
echo
echo "[dev] Tip: export PHOS_CAMERA_MOCK=true before starting backend for local testing."
