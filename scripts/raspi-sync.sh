#!/usr/bin/env bash

set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
RPI_HOST="${RPI_HOST:-raspi-2}"
RPI_USER="${RPI_USER:-millan}"
RPI_REPO_DIR="${RPI_REPO_DIR:-/home/millan/Dev/phos-project}"

echo "[raspi-sync] Syncing repository to ${RPI_USER}@${RPI_HOST}:${RPI_REPO_DIR}"
rsync -az --delete \
  --exclude ".git" \
  --exclude ".venv" \
  --exclude "node_modules" \
  --exclude "phos-engine/data" \
  --exclude "phos-portal/dist" \
  "${ROOT_DIR}/" "${RPI_USER}@${RPI_HOST}:${RPI_REPO_DIR}/"

echo "[raspi-sync] Done."
