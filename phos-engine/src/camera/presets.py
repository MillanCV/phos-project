from __future__ import annotations

from dataclasses import dataclass

from src.shared.errors import NotFoundError


@dataclass(slots=True, frozen=True)
class CameraScriptPreset:
    name: str
    description: str
    commands: list[str]
    timeout_seconds: int = 30


_PRESETS: dict[str, CameraScriptPreset] = {
    "health_check": CameraScriptPreset(
        name="health_check",
        description="Valida conexion y responde al runtime CHDKPTP.",
        commands=["luar return get_mode()"],
        timeout_seconds=10,
    ),
    "switch_record_mode": CameraScriptPreset(
        name="switch_record_mode",
        description="Cambia la camara a modo record.",
        commands=["rec"],
        timeout_seconds=10,
    ),
    "switch_playback_mode": CameraScriptPreset(
        name="switch_playback_mode",
        description="Cambia la camara a modo playback.",
        commands=["play"],
        timeout_seconds=10,
    ),
    "dcim_probe": CameraScriptPreset(
        name="dcim_probe",
        description="Lista directorio DCIM para comprobar acceso remoto.",
        commands=['ls "A/DCIM"'],
        timeout_seconds=10,
    ),
}


def list_presets() -> list[CameraScriptPreset]:
    return sorted(_PRESETS.values(), key=lambda preset: preset.name)


def get_preset(name: str) -> CameraScriptPreset:
    preset = _PRESETS.get(name)
    if not preset:
        raise NotFoundError(f"camera preset {name} not found")
    return preset
