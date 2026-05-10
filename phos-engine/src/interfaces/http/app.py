from __future__ import annotations

import os
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware

from src.infrastructure.logging import configure_logging, get_logger
from src.interfaces.http.container import build_container
from src.interfaces.http.errors import register_exception_handlers
from src.interfaces.http.routers import (
    camera_router,
    capture_router,
    health_router,
    solar_router,
    system_router,
    timelapse_router,
)


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
    app.include_router(system_router)
    app.include_router(solar_router)

    return app
