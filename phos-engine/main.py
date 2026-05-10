from datetime import datetime, timezone
import os
import socket

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel


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


if __name__ == "__main__":
    import uvicorn

    uvicorn.run(
        "main:app",
        host=os.getenv("PHOS_HOST", "0.0.0.0"),
        port=int(os.getenv("PHOS_PORT", "8000")),
    )
