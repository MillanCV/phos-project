#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"

RPI_HOST="${RPI_HOST:-raspi-2}"
RPI_USER="${RPI_USER:-millan}"
RPI_REPO_DIR="${RPI_REPO_DIR:-/home/millan/Dev/phos-project}"

PHOS_BACKEND_PORT="${PHOS_BACKEND_PORT:-8001}"
PHOS_FRONTEND_PORT="${PHOS_FRONTEND_PORT:-5174}"
PHOS_BACKEND_HOST="${PHOS_BACKEND_HOST:-127.0.0.1}"
PHOS_FRONTEND_HOST="${PHOS_FRONTEND_HOST:-127.0.0.1}"
PHOS_CAMERA_MOCK="${PHOS_CAMERA_MOCK:-false}"
CHDKPTP_BIN="${CHDKPTP_BIN:-/home/millan/chdkptp_tool/chdkptp-r964/chdkptp.sh}"
# Logging (match phos-engine defaults; override when calling raspi-dev-up from your laptop).
PHOS_LOG_LEVEL="${PHOS_LOG_LEVEL:-DEBUG}"
PHOS_LOG_COLOR="${PHOS_LOG_COLOR:-1}"
PHOS_UVICORN_ACCESS_LOG="${PHOS_UVICORN_ACCESS_LOG:-1}"
PHOS_CAMERA_COMMAND_LOG="${PHOS_CAMERA_COMMAND_LOG:-full}"

# Local ports exposed through tunnel for browser/testing.
LOCAL_BACKEND_PORT="${LOCAL_BACKEND_PORT:-8001}"
LOCAL_FRONTEND_PORT="${LOCAL_FRONTEND_PORT:-5174}"

# Set SKIP_SYNC=1 if you only want restart+tunnel.
SKIP_SYNC="${SKIP_SYNC:-0}"
SSH_OPTS="${SSH_OPTS:--o BatchMode=yes -o ConnectTimeout=10}"
NPM_INSTALL_MODE="${NPM_INSTALL_MODE:-auto}"
STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS:-90}"
STARTUP_POLL_INTERVAL_SECONDS="${STARTUP_POLL_INTERVAL_SECONDS:-2}"

echo "[raspi-dev-up] Host: ${RPI_USER}@${RPI_HOST}"
echo "[raspi-dev-up] Remote repo: ${RPI_REPO_DIR}"
echo "[raspi-dev-up] Remote backend/frontend ports: ${PHOS_BACKEND_PORT}/${PHOS_FRONTEND_PORT}"
echo "[raspi-dev-up] Remote backend/frontend host: ${PHOS_BACKEND_HOST}/${PHOS_FRONTEND_HOST}"
echo "[raspi-dev-up] Startup timeout/poll: ${STARTUP_TIMEOUT_SECONDS}s/${STARTUP_POLL_INTERVAL_SECONDS}s"
echo "[raspi-dev-up] Remote log file: ssh ${RPI_USER}@${RPI_HOST} 'tail -f /tmp/phos-dev-backend.log'"

if [[ "${SKIP_SYNC}" != "1" ]]; then
  echo "[raspi-dev-up] Syncing files..."
  "${ROOT_DIR}/scripts/raspi-sync.sh"
else
  echo "[raspi-dev-up] SKIP_SYNC=1, skipping rsync."
fi

echo "[raspi-dev-up] Restarting backend/frontend on Raspberry..."
ssh ${SSH_OPTS} "${RPI_USER}@${RPI_HOST}" env \
  RPI_REPO_DIR="${RPI_REPO_DIR}" \
  PHOS_BACKEND_PORT="${PHOS_BACKEND_PORT}" \
  PHOS_FRONTEND_PORT="${PHOS_FRONTEND_PORT}" \
  PHOS_BACKEND_HOST="${PHOS_BACKEND_HOST}" \
  PHOS_FRONTEND_HOST="${PHOS_FRONTEND_HOST}" \
  PHOS_CAMERA_MOCK="${PHOS_CAMERA_MOCK}" \
  CHDKPTP_BIN="${CHDKPTP_BIN}" \
  PHOS_LOG_LEVEL="${PHOS_LOG_LEVEL}" \
  PHOS_LOG_COLOR="${PHOS_LOG_COLOR}" \
  PHOS_UVICORN_ACCESS_LOG="${PHOS_UVICORN_ACCESS_LOG}" \
  PHOS_CAMERA_COMMAND_LOG="${PHOS_CAMERA_COMMAND_LOG}" \
  NPM_INSTALL_MODE="${NPM_INSTALL_MODE}" \
  STARTUP_TIMEOUT_SECONDS="${STARTUP_TIMEOUT_SECONDS}" \
  STARTUP_POLL_INTERVAL_SECONDS="${STARTUP_POLL_INTERVAL_SECONDS}" \
  /bin/bash <<'EOF'
set -euo pipefail

echo "[remote] backend: cd ${RPI_REPO_DIR}/phos-engine"
cd "${RPI_REPO_DIR}/phos-engine"
echo "[remote] backend: uv sync"
/home/millan/.local/bin/uv sync

echo "[remote] backend: stop old process on ${PHOS_BACKEND_PORT}"
pkill -f "uvicorn main:app --host ${PHOS_BACKEND_HOST} --port ${PHOS_BACKEND_PORT}" || true
pkill -f "uvicorn main:app --host 127.0.0.1 --port ${PHOS_BACKEND_PORT}" || true
pkill -f "uvicorn main:app --host 0.0.0.0 --port ${PHOS_BACKEND_PORT}" || true
if command -v ss >/dev/null 2>&1; then
  BACKEND_PIDS="$(ss -ltnp 2>/dev/null | awk '/:'"${PHOS_BACKEND_PORT}"'\\b/ {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
  if [[ -n "${BACKEND_PIDS}" ]]; then
    echo "[remote] backend: force-kill listeners on ${PHOS_BACKEND_PORT}: ${BACKEND_PIDS}"
    kill -9 ${BACKEND_PIDS} || true
  fi
fi

echo "[remote] backend: start dev server (logs: tail -f /tmp/phos-dev-backend.log)"
UVICORN_ACCESS=(--access-log)
if [[ "${PHOS_UVICORN_ACCESS_LOG:-}" =~ ^(0|false|no|off|never)$ ]]; then
  UVICORN_ACCESS=(--no-access-log)
fi
nohup env \
  PHOS_LOG_LEVEL="${PHOS_LOG_LEVEL}" \
  PHOS_LOG_COLOR="${PHOS_LOG_COLOR}" \
  PHOS_UVICORN_ACCESS_LOG="${PHOS_UVICORN_ACCESS_LOG}" \
  PHOS_CAMERA_COMMAND_LOG="${PHOS_CAMERA_COMMAND_LOG}" \
  PHOS_CAMERA_MOCK="${PHOS_CAMERA_MOCK}" \
  CHDKPTP_BIN="${CHDKPTP_BIN}" \
  /home/millan/.local/bin/uv run python -m uvicorn main:app --reload --host "${PHOS_BACKEND_HOST}" --port "${PHOS_BACKEND_PORT}" "${UVICORN_ACCESS[@]}" > /tmp/phos-dev-backend.log 2>&1 &

echo "[remote] frontend: cd ${RPI_REPO_DIR}/phos-portal"
cd "${RPI_REPO_DIR}/phos-portal"
if [[ "${NPM_INSTALL_MODE}" == "always" || ( "${NPM_INSTALL_MODE}" == "auto" && ! -d node_modules ) ]]; then
  echo "[remote] frontend: npm install"
  npm install --no-fund --no-audit
else
  echo "[remote] frontend: skipping npm install (NPM_INSTALL_MODE=${NPM_INSTALL_MODE})"
fi

echo "[remote] frontend: stop old process on ${PHOS_FRONTEND_PORT}"
pkill -f "vite --host ${PHOS_FRONTEND_HOST} --port ${PHOS_FRONTEND_PORT}" || true
pkill -f "vite --host 127.0.0.1 --port ${PHOS_FRONTEND_PORT}" || true
pkill -f "vite --host 0.0.0.0 --port ${PHOS_FRONTEND_PORT}" || true
if command -v ss >/dev/null 2>&1; then
  FRONTEND_PIDS="$(ss -ltnp 2>/dev/null | awk '/:'"${PHOS_FRONTEND_PORT}"'\\b/ {print $NF}' | sed -n 's/.*pid=\([0-9]\+\).*/\1/p' | sort -u)"
  if [[ -n "${FRONTEND_PIDS}" ]]; then
    echo "[remote] frontend: force-kill listeners on ${PHOS_FRONTEND_PORT}: ${FRONTEND_PIDS}"
    kill -9 ${FRONTEND_PIDS} || true
  fi
fi

echo "[remote] frontend: start dev server"
nohup env VITE_API_BASE_URL="http://127.0.0.1:${PHOS_BACKEND_PORT}/api" npm run dev -- --host "${PHOS_FRONTEND_HOST}" --port "${PHOS_FRONTEND_PORT}" > /tmp/phos-dev-frontend.log 2>&1 &

wait_http() {
  local name="$1"
  local url="$2"
  local timeout_seconds="$3"
  local poll_seconds="$4"
  local elapsed=0
  echo "[remote] waiting for ${name} (max ${timeout_seconds}s, poll ${poll_seconds}s): ${url}"
  while (( elapsed < timeout_seconds )); do
    if curl -fsS "$url" >/dev/null 2>&1; then
      echo "[remote] ${name} is ready: ${url}"
      return 0
    fi
    if (( elapsed % 10 == 0 )); then
      echo "[remote] ${name} not answering yet (${elapsed}s / ${timeout_seconds}s)"
    fi
    sleep "$poll_seconds"
    elapsed=$((elapsed + poll_seconds))
  done
  echo "[remote] ERROR: ${name} did not become ready within ${timeout_seconds}s (${url})"
  return 1
}

wait_http "backend" "http://127.0.0.1:${PHOS_BACKEND_PORT}/api/health" "${STARTUP_TIMEOUT_SECONDS}" "${STARTUP_POLL_INTERVAL_SECONDS}"
wait_http "frontend" "http://127.0.0.1:${PHOS_FRONTEND_PORT}" "${STARTUP_TIMEOUT_SECONDS}" "${STARTUP_POLL_INTERVAL_SECONDS}"
EOF

echo "[raspi-dev-up] Ensuring local SSH tunnel..."
pkill -f "ssh .*${LOCAL_BACKEND_PORT}:127.0.0.1:${PHOS_BACKEND_PORT}.*${LOCAL_FRONTEND_PORT}:127.0.0.1:${PHOS_FRONTEND_PORT}.*${RPI_USER}@${RPI_HOST}" || true
ssh ${SSH_OPTS} -f -N \
  -L "${LOCAL_BACKEND_PORT}:127.0.0.1:${PHOS_BACKEND_PORT}" \
  -L "${LOCAL_FRONTEND_PORT}:127.0.0.1:${PHOS_FRONTEND_PORT}" \
  "${RPI_USER}@${RPI_HOST}"

echo
echo "[raspi-dev-up] Ready."
echo "  Frontend: http://127.0.0.1:${LOCAL_FRONTEND_PORT}"
echo "  Backend:  http://127.0.0.1:${LOCAL_BACKEND_PORT}/api/health"
echo
echo "[raspi-dev-up] Remote logs:"
echo "  ssh ${RPI_USER}@${RPI_HOST} 'tail -f /tmp/phos-dev-backend.log'"
echo "  ssh ${RPI_USER}@${RPI_HOST} 'tail -f /tmp/phos-dev-frontend.log'"
