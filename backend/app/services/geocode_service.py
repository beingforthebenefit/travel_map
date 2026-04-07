import asyncio
import time

import httpx

from app.config import settings

_last_request_time: float = 0.0
_lock = asyncio.Lock()

NOMINATIM_URL = "https://nominatim.openstreetmap.org/search"


async def geocode(query: str) -> list[dict]:
    global _last_request_time

    async with _lock:
        # Enforce 1 req/sec rate limit
        now = time.monotonic()
        elapsed = now - _last_request_time
        if elapsed < 1.0:
            await asyncio.sleep(1.0 - elapsed)
        _last_request_time = time.monotonic()

    params = {
        "q": query,
        "format": "json",
        "limit": 5,
        "addressdetails": 0,
    }
    headers = {"User-Agent": settings.nominatim_user_agent}

    async with httpx.AsyncClient() as client:
        try:
            resp = await client.get(NOMINATIM_URL, params=params, headers=headers, timeout=10)
            resp.raise_for_status()
            data = resp.json()
            return [
                {
                    "display_name": item["display_name"],
                    "lat": float(item["lat"]),
                    "lon": float(item["lon"]),
                }
                for item in data
            ]
        except (httpx.HTTPError, KeyError, ValueError):
            return []
