# CHDK + CHDKPTP Quick Guide

This guide explains the minimum setup and daily workflow to run `phos-engine` with a CHDK-enabled Canon camera controlled through CHDKPTP.

## What are CHDK and CHDKPTP

- **CHDK** is an add-on firmware loaded from the SD card that enables scripting and extended camera control features.
- **CHDKPTP** is the command-line/remote control tool used by this backend to send commands, execute scripts, and transfer files.

## Minimum setup

1. Install CHDK on the SD card for your camera model.
2. Confirm camera boots with CHDK enabled.
3. Install `chdkptp` on the host running `phos-engine`.
4. Connect camera over USB.

## Environment variables used by this backend

- `CHDKPTP_BIN`: binary name/path for CHDKPTP (default: `chdkptp`)
- `PHOS_CAMERA_MOCK`: `true` to run without a physical camera
- `PHOS_DATA_DIR`: local storage path for captures and metadata
- `PHOS_HOST`, `PHOS_PORT`: API bind host/port

## CHDKPTP commands used by current implementation

The camera gateway currently uses these operations:

- Detect camera list: `chdkptp -elist`
- Switch camera mode:
  - record: `-e rec`
  - playback: `-e play`
- Single capture and download:
  - `-e rec -e shoot -e 'download -s A/DCIM/100CANON/IMG_0001.JPG "<local_file>"'`
- Download arbitrary file:
  - `-e 'download -s "<remote_path>" "<local_path>"'`
- List remote directory:
  - `-e 'ls "<remote_dir>"'`
- Run script profile commands:
  - sequence passed as repeated `-e <command>`

## API quick flow by mode

### Normal capture

1. Check camera: `GET /api/camera/status`
2. Capture photo: `POST /api/capture/photo`
3. Read latest metadata: `GET /api/capture/latest`

### Timelapse

1. Create plan: `POST /api/timelapse/plans`
2. Start plan: `POST /api/timelapse/plans/{plan_id}/start`
3. Stop plan: `POST /api/timelapse/plans/{plan_id}/stop`

### Lightning mode

1. Start session: `POST /api/lightning/sessions`
2. Get session: `GET /api/lightning/sessions/{session_id}`
3. Stop session: `POST /api/lightning/sessions/{session_id}/stop`

### Motion mode

1. Start session: `POST /api/motion/sessions`
2. Get session: `GET /api/motion/sessions/{session_id}`
3. Stop session: `POST /api/motion/sessions/{session_id}/stop`

### Direct script control (camera slice)

1. Run script profile: `POST /api/camera/scripts/run`
2. Poll status: `GET /api/camera/scripts/{run_id}`
3. Stop run: `POST /api/camera/scripts/{run_id}/stop`

## Troubleshooting

- **`chdkptp not found in PATH`**
  - Set `CHDKPTP_BIN` to the absolute binary path.
- **Camera disconnected / no cameras**
  - Verify USB cable, camera mode, and OS USB permissions.
- **Capture succeeded but local file missing**
  - Verify remote source path and write permissions in `PHOS_DATA_DIR`.
- **Script run fails**
  - Inspect `stderr` and `stdout` from `/api/camera/scripts/{run_id}`.
- **Need backend-only testing**
  - Set `PHOS_CAMERA_MOCK=true`.

## Official references

- CHDKPTP Scripting Guide: <https://app.assembla.com/spaces/chdkptp/wiki/Scripting_Guide>
- CHDKPTP CLI Quickstart: <https://app.assembla.com/spaces/chdkptp/wiki/CLI_Quickstart>
- CHDKPTP DNG Processing: <https://app.assembla.com/spaces/chdkptp/wiki/DNG_Processing>
- CHDK wiki: <https://chdk.fandom.com/wiki/CHDK>
- CHDK Time Lapse Script One: <https://chdk.fandom.com/wiki/Time_Lapse_Script_One>
- CHDK Lightning script reference: <https://chdk.fandom.com/wiki/UBASIC/Scripts:_Lightning_Photography>
