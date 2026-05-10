# Phos

Phos is an automated observatory and camera control system designed for Raspberry Pi 2. It uses CHDK to control Canon cameras for dynamic timelapses and real time remote monitoring.

## Project Structure

This monorepo follows Clean Architecture principles.

phos engine: Backend API built with Python 3.11 and FastAPI managed by uv.
phos portal: Frontend Dashboard built with React TypeScript and Vite.
github: CI CD pipelines for automated deployment to the Pi via Tailscale.

## Local Development Mac

### Prerequisites
uv installed.
Node.js and npm installed.

### Start the system
Open two terminals in the root directory.

#### Terminal 1 Backend
`cd phos-engine && uv run uvicorn main:app --reload --host 0.0.0.0 --port 8000`

#### Terminal 2 Frontend
`cd phos-portal && npm install && npm run dev`

The frontend calls the backend at `/api/status` (proxied to `http://127.0.0.1:8000` in dev).

## Deployment to Raspberry Pi 2

Deployment is handled automatically via GitHub Actions whenever you push to `main`.
The workflow builds `phos-portal` and restarts the backend service that serves the built frontend.

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
