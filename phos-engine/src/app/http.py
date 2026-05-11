from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.app.container import build_container
from src.app.errors import register_exception_handlers
from src.app.health import router as health_router
from src.camera.router import router as camera_router
from src.capture.router import router as capture_router
from src.lightning.router import router as lightning_router
from src.motion.router import router as motion_router
from src.shared.logging import configure_logging, get_logger
from src.solar.router import router as solar_router
from src.system.router import router as system_router
from src.timelapse.router import router as timelapse_router


def create_app() -> FastAPI:
    configure_logging()
    logger = get_logger("phos.api")

    app = FastAPI(title="Phos Engine", version="0.1.0")
    app.state.container = build_container()

    allowed_origins = [origin.strip() for origin in os.getenv("PHOS_ALLOWED_ORIGINS", "*").split(",") if origin.strip()]
    app.add_middleware(
        CORSMiddleware,
        allow_origins=allowed_origins or ["*"],
        allow_credentials=False,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.middleware("http")
    async def add_request_id(request: Request, call_next):
        request_id = request.headers.get("x-request-id", str(uuid4()))
        response = await call_next(request)
        response.headers["x-request-id"] = request_id
        logger.info("request completed", extra={"request_id": request_id, "path": request.url.path})
        return response

    register_exception_handlers(app)
    app.include_router(health_router)
    app.include_router(camera_router)
    app.include_router(capture_router)
    app.include_router(timelapse_router)
    app.include_router(lightning_router)
    app.include_router(motion_router)
    app.include_router(system_router)
    app.include_router(solar_router)

    return app
