# phos-engine

Backend service for camera automation and capture workflows (normal capture, timelapse, lightning, motion) with CHDK/CHDKPTP integration.

## Quick start

- Run tests: `python -m pytest tests -q`
- Start API: `python main.py`
- Use mock camera mode when hardware is unavailable: `PHOS_CAMERA_MOCK=true`

## CHDK / CHDKPTP documentation

- Project quick guide: [`docs/chdk-chdkptp-quick-guide.md`](docs/chdk-chdkptp-quick-guide.md)
- CHDK scripting capabilities catalog: [`docs/chdk-scripting-capabilities.md`](docs/chdk-scripting-capabilities.md)
- CHDKPTP Scripting Guide: <https://app.assembla.com/spaces/chdkptp/wiki/Scripting_Guide>
- CHDKPTP CLI Quickstart: <https://app.assembla.com/spaces/chdkptp/wiki/CLI_Quickstart>
- CHDKPTP DNG Processing: <https://app.assembla.com/spaces/chdkptp/wiki/DNG_Processing>
- CHDK wiki: <https://chdk.fandom.com/wiki/CHDK>
- CHDK Time Lapse Script One: <https://chdk.fandom.com/wiki/Time_Lapse_Script_One>
- CHDK Lightning script reference: <https://chdk.fandom.com/wiki/UBASIC/Scripts:_Lightning_Photography>
