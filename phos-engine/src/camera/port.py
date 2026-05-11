from __future__ import annotations

from src.camera.ports import CameraControlPort, CameraScriptPort, CameraTransferPort

# Backward-compatible alias used by existing slices/tests.
CameraGateway = CameraControlPort

__all__ = ["CameraGateway", "CameraControlPort", "CameraScriptPort", "CameraTransferPort"]
