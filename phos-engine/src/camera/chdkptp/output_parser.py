from __future__ import annotations

from src.camera.domain import ScriptRunState


def parse_script_state(returncode: int) -> ScriptRunState:
    if returncode == 0:
        return "completed"
    return "failed"


def collect_artifacts(expected_artifacts: list[str], stdout: str) -> list[str]:
    if not expected_artifacts:
        return []
    emitted: list[str] = []
    for artifact in expected_artifacts:
        if artifact in stdout:
            emitted.append(artifact)
    return emitted
