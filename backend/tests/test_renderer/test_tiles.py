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
