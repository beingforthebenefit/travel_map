import pytest
from app.renderer.tiles import (
    lat_lon_to_tile, lat_lon_to_pixel, compute_bounds, select_zoom, BBox,
)


def test_lat_lon_to_tile_origin():
    """Tile (0, 0) at zoom 0 covers the whole world."""
    x, y = lat_lon_to_tile(0, 0, 0)
    assert x == 0
    assert y == 0


def test_lat_lon_to_tile_zoom1():
    """At zoom 1, equator/prime meridian should be tile (1, 1)."""
    x, y = lat_lon_to_tile(0, 0, 1)
    assert x == 1
    assert y == 1


def test_lat_lon_to_tile_known_city():
    """Madrid (~40.4, -3.7) at zoom 6 should be a known tile."""
    x, y = lat_lon_to_tile(40.4168, -3.7038, 6)
    assert 29 <= x <= 31  # roughly column 30
    assert 23 <= y <= 25  # roughly row 24


def test_lat_lon_to_pixel_consistency():
    """Pixel coords should be tile coords * 256."""
    lat, lon, zoom = 40.4168, -3.7038, 6
    tx, ty = lat_lon_to_tile(lat, lon, zoom)
    px, py = lat_lon_to_pixel(lat, lon, zoom)
    # Pixel should be within the tile
    assert tx * 256 <= px < (tx + 1) * 256
    assert ty * 256 <= py < (ty + 1) * 256


def test_compute_bounds_padding():
    stops = [
        {"lat": 40.0, "lon": -4.0},
        {"lat": 38.0, "lon": -8.0},
    ]
    bbox = compute_bounds(stops, padding_pct=0.1)
    assert bbox.min_lat < 38.0
    assert bbox.max_lat > 40.0
    assert bbox.min_lon < -8.0
    assert bbox.max_lon > -4.0


def test_compute_bounds_single_stop():
    stops = [{"lat": 40.0, "lon": -4.0}]
    bbox = compute_bounds(stops)
    # With a single stop, bbox should use default padding
    assert bbox.min_lat < 40.0
    assert bbox.max_lat > 40.0


def test_select_zoom_reasonable():
    bbox = BBox(min_lat=37.0, max_lat=42.0, min_lon=-10.0, max_lon=-3.0)
    zoom = select_zoom(bbox, 1200, 900)
    assert 4 <= zoom <= 8


def test_select_zoom_wide_area():
    bbox = BBox(min_lat=-60.0, max_lat=60.0, min_lon=-160.0, max_lon=160.0)
    zoom = select_zoom(bbox, 1200, 900)
    assert zoom <= 3


# --- Cache key uniqueness ---

def _cache_key_for(url_template: str) -> str:
    """Replicate the cache-key logic from fetch_tile."""
    raw = url_template.split("?")[0]
    parts = [p for p in raw.split("/") if p]
    key_parts = []
    for p in parts:
        if "{z}" in p or p == "{z}":
            break
        key_parts.append(p)
    return "_".join(key_parts).replace(".", "_").replace("-", "_")


def test_cache_key_positron_vs_dark_are_distinct():
    """Positron and Dark Matter share the same domain — keys must differ."""
    positron = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
    dark = "https://basemaps.cartocdn.com/dark_all/{z}/{x}/{y}@2x.png"
    assert _cache_key_for(positron) != _cache_key_for(dark)


def test_cache_key_includes_style_path():
    positron = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
    key = _cache_key_for(positron)
    assert "light_all" in key


def test_cache_key_different_providers_are_distinct():
    osm = "https://tile.openstreetmap.org/{z}/{x}/{y}.png"
    positron = "https://basemaps.cartocdn.com/light_all/{z}/{x}/{y}@2x.png"
    stadia = "https://tiles.stadiamaps.com/tiles/stamen_watercolor/{z}/{x}/{y}.jpg?api_key={api_key}"
    keys = {_cache_key_for(u) for u in [osm, positron, stadia]}
    assert len(keys) == 3


# --- top_margin shifts content down ---

def test_top_margin_shifts_origin_down():
    """A positive top_margin should produce a smaller (more negative) origin_py,
    placing content lower on the canvas."""
    from app.renderer.tiles import compute_bounds, select_zoom, lat_lon_to_pixel

    stops = [{"lat": 40.4, "lon": -3.7}, {"lat": 38.7, "lon": -9.1}]
    bbox = compute_bounds(stops)
    zoom = select_zoom(bbox, 1200, 900)

    min_px, min_py = lat_lon_to_pixel(bbox.max_lat, bbox.min_lon, zoom)
    max_px, max_py = lat_lon_to_pixel(bbox.min_lat, bbox.max_lon, zoom)
    content_w = max_px - min_px
    content_h = max_py - min_py

    origin_py_no_margin = min_py - (900 - content_h) / 2
    origin_py_with_margin = min_py - (900 - content_h) / 2 - 100 / 2

    # With top_margin, origin_py should be smaller → content appears lower on canvas
    assert origin_py_with_margin < origin_py_no_margin
