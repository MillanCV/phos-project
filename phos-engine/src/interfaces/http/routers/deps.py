from __future__ import annotations

from fastapi import Request

from src.interfaces.http.container import ApiContainer


def get_container(request: Request) -> ApiContainer:
    return request.app.state.container
