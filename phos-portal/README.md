# Phos Portal

Minimal frontend dashboard for Phos.

## Features

- Camera connection status
- Manual capture trigger and latest capture info
- Timelapse fixed-interval plan with window schedule
- System metrics panel (disk, CPU load, temperature, uptime)

## Run locally

1. Copy env template:

   `cp .env.example .env`

2. Install and start dev server:

   `npm install && npm run dev`

By default, frontend calls backend at `http://127.0.0.1:8000` using `VITE_API_BASE_URL`.
In production behind reverse proxy, use `VITE_API_BASE_URL=/api`.

## Build

`npm run build`
