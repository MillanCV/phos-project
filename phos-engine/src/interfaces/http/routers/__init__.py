from .camera import router as camera_router
from .capture import router as capture_router
from .health import router as health_router
from .solar import router as solar_router
from .system import router as system_router
from .timelapse import router as timelapse_router

__all__ = [
    "health_router",
    "camera_router",
    "capture_router",
    "timelapse_router",
    "system_router",
    "solar_router",
]
