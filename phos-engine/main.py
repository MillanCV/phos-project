from datetime import datetime, timezone
import os
from pathlib import Path
import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel


BASE_DIR = Path(__file__).resolve().parent.parent
FRONTEND_DIST_DIR = BASE_DIR / "phos-portal" / "dist"

app = FastAPI(title="Phos Engine", version="0.1.0")

allowed_origins = [
    origin.strip()
    for origin in os.getenv("PHOS_ALLOWED_ORIGINS", "*").split(",")
    if origin.strip()
]
app.add_middleware(
    CORSMiddleware,
    allow_origins=allowed_origins or ["*"],
    allow_credentials=False,
    allow_methods=["*"],
    allow_headers=["*"],
)


class StatusResponse(BaseModel):
    message: str
    hostname: str
    timestamp_utc: str


@app.get("/api/health")
def health() -> dict[str, str]:
    return {"status": "ok"}


@app.get("/api/status", response_model=StatusResponse)
def status() -> StatusResponse:
    return StatusResponse(
        message="Phos backend activo",
        hostname=socket.gethostname(),
        timestamp_utc=datetime.now(timezone.utc).isoformat(),
    )


if FRONTEND_DIST_DIR.exists():

    @app.get("/", include_in_schema=False)
    def serve_index() -> FileResponse:
        return FileResponse(FRONTEND_DIST_DIR / "index.html")


    @app.get("/{file_path:path}", include_in_schema=False)
    def serve_spa(file_path: str) -> FileResponse:
        requested_file = FRONTEND_DIST_DIR / file_path
        if requested_file.is_file():
            return FileResponse(requested_file)
        return FileResponse(FRONTEND_DIST_DIR / "index.html")


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("PHOS_HOST", "0.0.0.0"),
        port=int(os.getenv("PHOS_PORT", "8000")),
    )
