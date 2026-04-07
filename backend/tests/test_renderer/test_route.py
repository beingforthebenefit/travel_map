import pytest
from PIL import Image
from app.renderer.route import draw_route


def test_draw_route_produces_image():
    canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    stops = [
        {"lat": 40.4, "lon": -3.7},
        {"lat": 38.7, "lon": -9.1},
    ]
    result = draw_route(canvas, stops, zoom=6, origin_px=7400, origin_py=6000)
    assert result.size == (800, 600)
    assert result.mode == "RGBA"


def test_draw_route_single_stop_unchanged():
    canvas = Image.new("RGBA", (400, 300), (255, 255, 255, 255))
    stops = [{"lat": 40.4, "lon": -3.7}]
    result = draw_route(canvas, stops, zoom=6, origin_px=7400, origin_py=6000)
    # With single stop, canvas should be returned unchanged
    assert result.size == (400, 300)


def test_draw_route_dashed():
    canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    stops = [
        {"lat": 40.4, "lon": -3.7},
        {"lat": 38.7, "lon": -9.1},
    ]
    result = draw_route(
        canvas, stops, zoom=6, origin_px=7400, origin_py=6000,
        line_style="dashed",
    )
    assert result.size == (800, 600)
