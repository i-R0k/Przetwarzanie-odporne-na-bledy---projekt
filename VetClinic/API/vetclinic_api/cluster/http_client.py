from __future__ import annotations

from typing import AsyncGenerator

import httpx


async def get_http_client() -> AsyncGenerator[httpx.AsyncClient, None]:
    """
    Dependency for FastAPI that provides a shared AsyncClient
    for the duration of a request.
    """
    async with httpx.AsyncClient(timeout=5.0) as client:
        yield client
