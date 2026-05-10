# Phos

Phos is an automated observatory and camera control system designed for Raspberry Pi 2. It uses CHDK to control Canon cameras for dynamic timelapses and real time remote monitoring.

## Project Structure

This monorepo follows Clean Architecture principles.

phos engine: Backend API built with Python 3.11 and FastAPI managed by uv.
phos portal: Frontend Dashboard built with React TypeScript and Vite.
github: CI CD pipelines for automated deployment to the Pi via Tailscale.

### Backend Layers (`phos-engine/src`)

- `domain`: entities and business rules.
- `application`: use cases and ports.
- `infrastructure`: CHDKPTP, storage, scheduler, metrics adapters.
- `interfaces/http`: FastAPI routes and DTOs.

## Local Development Mac

### Prerequisites

uv installed.
Node.js and npm installed.

### Start the system

Open two terminals in the root directory.

#### Terminal 1 Backend

`cd phos-engine && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`

#### Terminal 2 Frontend

`cd phos-portal && cp .env.example .env && npm install && npm run dev`

The frontend and backend run independently:

- Backend API: `http://127.0.0.1:8000`
- Frontend app: `http://127.0.0.1:5173`

Frontend calls backend using `VITE_API_BASE_URL`.

### One-command local startup

`bash scripts/dev.sh`

This script now prints the two commands you should run in separate terminals.

Quick usage:

Terminal 1:
`bash scripts/dev-backend.sh`

Terminal 2:
`bash scripts/dev-frontend.sh`

Defaults:

- backend: `http://127.0.0.1:8000` (`PHOS_BACKEND_PORT`)
- frontend: `http://127.0.0.1:5173` (`PHOS_FRONTEND_PORT`)
- camera mode: `PHOS_CAMERA_MOCK=true` for local backend tests

### API V1 Endpoints

- `GET /api/camera/status`
- `POST /api/capture/photo`
- `GET /api/capture/latest`
- `POST /api/timelapse/plans`
- `POST /api/timelapse/plans/{id}/start`
- `POST /api/timelapse/plans/{id}/stop`
- `GET /api/timelapse/plans/{id}`
- `GET /api/system/metrics`
- `GET /api/solar/today`
- `GET /api/solar/range?days=30`
- `GET /api/solar/range/summary?days=30` (sunrise/sunset ranges + daylight/night stats)

## Deployment to Raspberry Pi 2

Deployment is handled automatically via GitHub Actions whenever you push to `main`.
The workflow builds `phos-portal`, syncs backend dependencies, and restarts backend plus optional frontend services.

Set repository variable `PHOS_API_BASE_URL` to `/api` when using reverse proxy on the same domain (recommended for production).
Set optional backend variables:

- `PHOS_ALLOWED_ORIGINS` (comma-separated origins)
- `PHOS_CAMERA_MOCK=true` (run without physical camera)
- `CHDKPTP_BIN` (custom binary path)
- `PHOS_LATITUDE` and `PHOS_LONGITUDE` (location for sunrise/sunset)
- `PHOS_TIMEZONE` (example: `Europe/Madrid`)
- `PHOS_LOCATION_NAME` (label for logs/cache)
- `PHOS_SOLAR_CACHE_DAYS` (pre-cached days on startup, default `30`)

### Requirements on the Pi

uv installed.
chdkptp binaries located at chdkptp tool.
User millan added to the plugdev group for USB access.
Tailscale active for secure remote access.

### GitHub Secrets

Set the following secrets in your repository settings.
PI HOST: Your Pi Tailscale IP.
PI USERNAME: millan.
PI SSH KEY: Your private SSH key.

## Technology Stack

Backend: Python FastAPI Pydantic.
Package Manager: uv Astral.
Frontend: React TypeScript Vite.
Camera Control: chdkptp.
Network: Tailscale Mesh VPN.
CI CD: GitHub Actions.

## License

Private Project. All rights reserved.
