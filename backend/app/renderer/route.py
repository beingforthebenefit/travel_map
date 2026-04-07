import math

import cairo
import numpy as np
from PIL import Image

from app.renderer.tiles import lat_lon_to_pixel


def draw_route(
    canvas: Image.Image,
    stops: list[dict],
    zoom: int,
    origin_px: float,
    origin_py: float,
    route_color: tuple[int, int, int, int] = (139, 69, 19, 200),
    shadow_color: tuple[int, int, int, int] = (0, 0, 0, 60),
    line_style: str = "solid",
    line_weight: float = 3.0,
    loop: bool = False,
    waypoints: list[tuple[float, float]] | None = None,
) -> Image.Image:
    """Draw route path on canvas using PyCairo.

    If `waypoints` is provided (list of (lat, lon) tuples from a road router),
    those are used instead of straight lines between stops.
    """
    if len(stops) < 2:
        return canvas

    w, h = canvas.size

    if waypoints:
        # Road route: convert each (lat, lon) waypoint to canvas pixels
        points = []
        for lat, lon in waypoints:
            px, py = lat_lon_to_pixel(lat, lon, zoom)
            points.append((px - origin_px, py - origin_py))
    else:
        # Straight lines between stops
        points = []
        for stop in stops:
            px, py = lat_lon_to_pixel(stop["lat"], stop["lon"], zoom)
            points.append((px - origin_px, py - origin_py))
        # Close the loop by connecting last stop back to first
        if loop and len(points) >= 2:
            points.append(points[0])

    # Create Cairo surface from numpy array
    arr = np.array(canvas.convert("RGBA"))
    # Cairo uses BGRA premultiplied alpha
    surface = cairo.ImageSurface(cairo.FORMAT_ARGB32, w, h)
    buf = surface.get_data()
    # Copy PIL RGBA into Cairo BGRA
    flat = np.ndarray(shape=(h, w, 4), dtype=np.uint8, buffer=buf)
    flat[:, :, 0] = arr[:, :, 2]  # B
    flat[:, :, 1] = arr[:, :, 1]  # G
    flat[:, :, 2] = arr[:, :, 0]  # R
    flat[:, :, 3] = arr[:, :, 3]  # A
    surface.mark_dirty()

    ctx = cairo.Context(surface)

    def _set_dash(ctx, style, weight):
        if style == "dashed":
            ctx.set_dash([weight * 4, weight * 2])
        elif style == "dotted":
            ctx.set_dash([weight, weight * 2])
        else:
            ctx.set_dash([])

    def _draw_path(ctx, points):
        ctx.move_to(points[0][0], points[0][1])
        for p in points[1:]:
            ctx.line_to(p[0], p[1])

    # Draw shadow
    ctx.save()
    _draw_path(ctx, [(p[0] + 2, p[1] + 2) for p in points])
    ctx.set_source_rgba(
        shadow_color[0] / 255, shadow_color[1] / 255,
        shadow_color[2] / 255, shadow_color[3] / 255,
    )
    ctx.set_line_width(line_weight + 2)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    _set_dash(ctx, line_style, line_weight)
    ctx.stroke()
    ctx.restore()

    # Draw main path
    ctx.save()
    _draw_path(ctx, points)
    ctx.set_source_rgba(
        route_color[0] / 255, route_color[1] / 255,
        route_color[2] / 255, route_color[3] / 255,
    )
    ctx.set_line_width(line_weight)
    ctx.set_line_cap(cairo.LINE_CAP_ROUND)
    ctx.set_line_join(cairo.LINE_JOIN_ROUND)
    _set_dash(ctx, line_style, line_weight)
    ctx.stroke()
    ctx.restore()

    # Draw directional arrows at segment midpoints
    arrow_size = max(8, line_weight * 3)
    for i in range(len(points) - 1):
        x1, y1 = points[i]
        x2, y2 = points[i + 1]
        mx = (x1 + x2) / 2
        my = (y1 + y2) / 2
        angle = math.atan2(y2 - y1, x2 - x1)

        ctx.save()
        ctx.translate(mx, my)
        ctx.rotate(angle)
        ctx.move_to(arrow_size / 2, 0)
        ctx.line_to(-arrow_size / 2, -arrow_size / 3)
        ctx.line_to(-arrow_size / 2, arrow_size / 3)
        ctx.close_path()
        ctx.set_source_rgba(
            route_color[0] / 255, route_color[1] / 255,
            route_color[2] / 255, route_color[3] / 255,
        )
        ctx.fill()
        ctx.restore()

    # Convert Cairo surface back to PIL
    result_arr = np.ndarray(shape=(h, w, 4), dtype=np.uint8, buffer=surface.get_data())
    result = np.zeros((h, w, 4), dtype=np.uint8)
    result[:, :, 0] = result_arr[:, :, 2]  # R
    result[:, :, 1] = result_arr[:, :, 1]  # G
    result[:, :, 2] = result_arr[:, :, 0]  # B
    result[:, :, 3] = result_arr[:, :, 3]  # A

    return Image.fromarray(result)
