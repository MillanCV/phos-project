from __future__ import annotations

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from src.shared.errors import CameraUnavailableError, NotFoundError, ValidationError


def register_exception_handlers(app: FastAPI) -> None:
    @app.exception_handler(CameraUnavailableError)
    async def camera_unavailable_handler(_, exc: CameraUnavailableError) -> JSONResponse:
        return JSONResponse(status_code=503, content={"detail": str(exc)})

    @app.exception_handler(ValidationError)
    async def validation_error_handler(_, exc: ValidationError) -> JSONResponse:
        return JSONResponse(status_code=400, content={"detail": str(exc)})

    @app.exception_handler(NotFoundError)
    async def not_found_handler(_, exc: NotFoundError) -> JSONResponse:
        return JSONResponse(status_code=404, content={"detail": str(exc)})
