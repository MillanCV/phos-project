from __future__ import annotations

from fastapi import Request

from src.app.container import ApiContainer


def get_container(request: Request) -> ApiContainer:
    return request.app.state.container
