from pydantic import BaseModel


class StatusResponse(BaseModel):
    message: str
    hostname: str
    timestamp_utc: str
