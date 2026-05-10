from pydantic import BaseModel, Field


class TimelapsePlanCreateRequest(BaseModel):
    interval_seconds: int = Field(ge=10, le=86400)
    window_start_hour: int = Field(ge=0, le=23)
    window_end_hour: int = Field(ge=0, le=23)


class TimelapsePlanResponse(BaseModel):
    id: str
    interval_seconds: int
    window_start_hour: int
    window_end_hour: int
    active: bool
    last_capture_at: str | None
