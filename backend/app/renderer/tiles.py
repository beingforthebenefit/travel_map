import asyncio
import math
import time
from dataclasses import dataclass
from pathlib import Path

import httpx
from PIL import Image

from app.config import settings

TILE_SIZE = 256


@dataclass
class BBox:
    min_lat: float
    max_lat: float
    min_lon: float
    max_lon: float


def lat_lon_to_tile(lat: float, lon: float, zoom: int) -> tuple[int, int]:
    """Convert lat/lon to tile coordinates at given zoom level."""
    n = 2 ** zoom
    x = int((lon + 180.0) / 360.0 * n)
    lat_rad = math.radians(lat)
    y = int((1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n)
    x = max(0, min(n - 1, x))
    y = max(0, min(n - 1, y))
    return x, y


def lat_lon_to_pixel(lat: float, lon: float, zoom: int) -> tuple[float, float]:
    """Convert lat/lon to absolute pixel coordinates at given zoom level."""
    n = 2 ** zoom
    px = (lon + 180.0) / 360.0 * n * TILE_SIZE
    lat_rad = math.radians(lat)
    py = (1.0 - math.asinh(math.tan(lat_rad)) / math.pi) / 2.0 * n * TILE_SIZE
    return px, py


def compute_bounds(stops: list[dict], padding_pct: float = 0.25) -> BBox:
    """Compute bounding box from stops with padding.

    The 25% padding ensures photo bubbles (above stops) and labels (below)
    aren't clipped at canvas edges.
    """
    lats = [s["lat"] for s in stops]
    lons = [s["lon"] for s in stops]
    min_lat, max_lat = min(lats), max(lats)
    min_lon, max_lon = min(lons), max(lons)

    lat_pad = (max_lat - min_lat) * padding_pct or 0.5
    lon_pad = (max_lon - min_lon) * padding_pct or 0.5

    return BBox(
        min_lat=min_lat - lat_pad,
        max_lat=max_lat + lat_pad,
        min_lon=min_lon - lon_pad,
        max_lon=max_lon + lon_pad,
    )


def select_zoom(bbox: BBox, canvas_width: int, canvas_height: int) -> int:
    """Pick optimal zoom level so the bbox fits in the canvas."""
    for zoom in range(18, 0, -1):
        min_px, max_py = lat_lon_to_pixel(bbox.max_lat, bbox.min_lon, zoom)
        max_px, min_py = lat_lon_to_pixel(bbox.min_lat, bbox.max_lon, zoom)
        w = max_px - min_px
        h = max_py - min_py
        if w <= canvas_width and h <= canvas_height:
            return zoom
    return 1


async def fetch_tile(
    url_template: str,
    z: int, x: int, y: int,
    api_key: str = "",
    cache_dir: Path | None = None,
) -> Image.Image:
    """Fetch a single tile with caching and retry logic."""
    # Check cache
    if cache_dir:
        # Build a stable provider key from all path segments before the {z} placeholder
        # (domain-only would collide for e.g. carto light_all vs dark_all)
        raw = url_template.split("?")[0]  # drop query string
        parts = [p for p in raw.split("/") if p]
        key_parts = []
        for p in parts:
            if "{z}" in p or p == "{z}":
                break
            key_parts.append(p)
        provider = "_".join(key_parts).replace(".", "_").replace("-", "_")
        cache_path = cache_dir / provider / str(z) / str(x) / f"{y}.png"
        if cache_path.exists():
            return Image.open(cache_path).convert("RGBA")

    url = url_template.format(z=z, x=x, y=y, api_key=api_key)

    for attempt in range(3):
        try:
            async with httpx.AsyncClient() as client:
                resp = await client.get(
                    url,
                    headers={"User-Agent": "travel_map/1.0"},
                    timeout=15,
                )
                resp.raise_for_status()
                from io import BytesIO
                img = Image.open(BytesIO(resp.content)).convert("RGBA")

                # Write to cache
                if cache_dir:
                    cache_path.parent.mkdir(parents=True, exist_ok=True)
                    img.save(cache_path, "PNG")

                return img
        except (httpx.HTTPError, Exception):
            if attempt < 2:
                await asyncio.sleep(0.5 * (2 ** attempt))
            else:
                # Return gray placeholder tile on failure
                return Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (200, 200, 200, 255))

    return Image.new("RGBA", (TILE_SIZE, TILE_SIZE), (200, 200, 200, 255))


async def fetch_and_stitch_tiles(
    stops: list[dict],
    canvas_width: int,
    canvas_height: int,
    url_template: str,
    api_key: str = "",
    progress_callback=None,
    top_margin: int = 0,
) -> tuple[Image.Image, int, float, float]:
    """Fetch tiles and stitch them into a canvas.

    Returns (canvas, zoom, origin_px, origin_py) where origin is the
    pixel offset of the top-left corner of the canvas in absolute tile coordinates.
    """
    bbox = compute_bounds(stops)
    zoom = select_zoom(bbox, canvas_width, canvas_height)

    # Compute the pixel range we need
    min_px, min_py = lat_lon_to_pixel(bbox.max_lat, bbox.min_lon, zoom)
    max_px, max_py = lat_lon_to_pixel(bbox.min_lat, bbox.max_lon, zoom)

    # Center the content in the canvas, shifting down by half of top_margin
    # so the title banner doesn't overlap map content
    content_w = max_px - min_px
    content_h = max_py - min_py
    origin_px = min_px - (canvas_width - content_w) / 2
    # Subtract top_margin/2 to shift map content down, leaving room for the banner
    origin_py = min_py - (canvas_height - content_h) / 2 - top_margin / 2

    # Determine tile range
    tile_x_start = int(origin_px // TILE_SIZE)
    tile_y_start = int(origin_py // TILE_SIZE)
    tile_x_end = int((origin_px + canvas_width) // TILE_SIZE)
    tile_y_end = int((origin_py + canvas_height) // TILE_SIZE)

    total_tiles = (tile_x_end - tile_x_start + 1) * (tile_y_end - tile_y_start + 1)
    fetched = 0

    cache_dir = Path(settings.data_dir) / "tile_cache"

    canvas = Image.new("RGBA", (canvas_width, canvas_height), (200, 200, 200, 255))

    for tx in range(tile_x_start, tile_x_end + 1):
        for ty in range(tile_y_start, tile_y_end + 1):
            tile = await fetch_tile(url_template, zoom, tx, ty, api_key, cache_dir)

            # Resize tile if needed (some providers serve @2x tiles)
            if tile.size != (TILE_SIZE, TILE_SIZE):
                tile = tile.resize((TILE_SIZE, TILE_SIZE), Image.LANCZOS)

            # Position tile on canvas
            paste_x = int(tx * TILE_SIZE - origin_px)
            paste_y = int(ty * TILE_SIZE - origin_py)
            canvas.paste(tile, (paste_x, paste_y))

            fetched += 1
            if progress_callback:
                progress_callback(fetched / total_tiles * 0.5)  # tiles are 50% of work

            # Small delay between requests
            await asyncio.sleep(0.05)

    return canvas, zoom, origin_px, origin_py
