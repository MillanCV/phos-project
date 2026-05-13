#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
BACKEND_DIR="$ROOT_DIR/phos-engine"
BACKEND_PORT="${PHOS_BACKEND_PORT:-8000}"
CHDKPTP_BIN="${CHDKPTP_BIN:-}"

if [[ -z "${PHOS_CAMERA_MOCK:-}" ]]; then
  if [[ -n "$CHDKPTP_BIN" ]]; then
    PHOS_CAMERA_MOCK="false"
  elif [[ -x "$HOME/chdkptp_tool/chdkptp-r964/chdkptp.sh" ]]; then
    CHDKPTP_BIN="$HOME/chdkptp_tool/chdkptp-r964/chdkptp.sh"
    PHOS_CAMERA_MOCK="false"
  elif command -v chdkptp >/dev/null 2>&1; then
    CHDKPTP_BIN="$(command -v chdkptp)"
    PHOS_CAMERA_MOCK="false"
  else
    PHOS_CAMERA_MOCK="true"
  fi
else
  PHOS_CAMERA_MOCK="${PHOS_CAMERA_MOCK}"
fi

if ! command -v uv >/dev/null 2>&1; then
  echo "[backend] 'uv' is required but not found."
  exit 1
fi

if [[ ! -d "$BACKEND_DIR" ]]; then
  echo "[backend] Could not find phos-engine directory."
  exit 1
fi

if command -v ss >/dev/null 2>&1; then
  if ss -ltn | grep -Eq "127\\.0\\.0\\.1:${BACKEND_PORT}\\b|0\\.0\\.0\\.0:${BACKEND_PORT}\\b"; then
    echo "[backend] Port ${BACKEND_PORT} is already in use."
    echo "[backend] Stop existing backend or set PHOS_BACKEND_PORT to a free port."
    exit 1
  fi
fi

echo "[backend] Starting on http://127.0.0.1:${BACKEND_PORT}"
echo "[backend] PHOS_CAMERA_MOCK=${PHOS_CAMERA_MOCK}"
echo "[backend] Defaults: verbose logs, colors, uvicorn access. Quiet later: PHOS_LOG_LEVEL=INFO PHOS_UVICORN_ACCESS_LOG=0 PHOS_HTTP_LOG_SKIP_PATHS=default PHOS_CAMERA_COMMAND_LOG=summary"
if [[ -n "$CHDKPTP_BIN" ]]; then
  echo "[backend] CHDKPTP_BIN=$CHDKPTP_BIN"
fi
cd "$BACKEND_DIR"
UVICORN_ACCESS=(--access-log)
if [[ "${PHOS_UVICORN_ACCESS_LOG:-}" =~ ^(0|false|no|off|never)$ ]]; then
  UVICORN_ACCESS=(--no-access-log)
fi
export PHOS_CAMERA_COMMAND_LOG="${PHOS_CAMERA_COMMAND_LOG:-full}"
PHOS_CAMERA_MOCK="$PHOS_CAMERA_MOCK" CHDKPTP_BIN="$CHDKPTP_BIN" uv run python -m uvicorn main:app --reload --host 127.0.0.1 --port "$BACKEND_PORT" "${UVICORN_ACCESS[@]}"
