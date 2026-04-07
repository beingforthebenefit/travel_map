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


def test_draw_route_with_waypoints():
    """When waypoints are provided, the route should still produce valid output."""
    canvas = Image.new("RGBA", (800, 600), (255, 255, 255, 255))
    stops = [
        {"lat": 40.4, "lon": -3.7},
        {"lat": 38.7, "lon": -9.1},
    ]
    # Provide explicit waypoints (road-following style)
    waypoints = [
        (40.4, -3.7),
        (40.0, -5.0),
        (39.0, -7.0),
        (38.7, -9.1),
    ]
    result = draw_route(
        canvas, stops, zoom=6, origin_px=7400, origin_py=6000,
        waypoints=waypoints,
    )
    assert result.size == (800, 600)
    assert result.mode == "RGBA"


def test_draw_route_waypoints_differ_from_straight():
    """A route drawn with waypoints should produce pixels different from straight-line."""
    canvas = Image.new("RGBA", (800, 600), (200, 200, 200, 255))
    stops = [{"lat": 40.4, "lon": -3.7}, {"lat": 38.7, "lon": -9.1}]

    straight = draw_route(canvas.copy(), stops, zoom=6, origin_px=7400, origin_py=6000)
    waypoints = [(40.4, -3.7), (39.5, -6.0), (38.7, -9.1)]
    with_wps = draw_route(canvas.copy(), stops, zoom=6, origin_px=7400, origin_py=6000,
                          waypoints=waypoints)

    import numpy as np
    arr_straight = np.array(straight)
    arr_wps = np.array(with_wps)
    # The two should not be identical
    assert not (arr_straight == arr_wps).all()
