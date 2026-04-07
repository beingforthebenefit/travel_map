from pathlib import Path
from typing import Callable

from PIL import Image

from app.renderer.tiles import fetch_and_stitch_tiles
from app.renderer.route import draw_route
from app.renderer.photos import composite_photos
from app.renderer.labels import place_labels, render_title_banner
from app.renderer.styles import get_style


async def generate_map(
    trip: dict,
    stops: list[dict],
    style_name: str = "watercolor",
    api_key: str = "",
    data_dir: str = "/data",
    progress_callback: Callable[[float], None] | None = None,
) -> Path:
    """Generate a print-ready map image.

    Returns the path to the output PNG file.
    """
    style = get_style(style_name)

    # Canvas dimensions from print settings
    dpi = trip.get("dpi", 300)
    print_w = trip.get("print_width", 24.0)
    print_h = trip.get("print_height", 18.0)
    canvas_width = int(print_w * dpi)
    canvas_height = int(print_h * dpi)

    # Scale all overlay elements relative to canvas size.
    # Base reference: 1200px wide preview. A 7200px canvas = 6× scale.
    scale = canvas_width / 1200

    def _progress(pct: float):
        if progress_callback:
            progress_callback(pct)

    # Stage 1-4: Fetch and stitch tiles
    _progress(0.0)
    canvas, zoom, origin_px, origin_py = await fetch_and_stitch_tiles(
        stops=stops,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        url_template=style.url_template,
        api_key=api_key,
        progress_callback=_progress,
    )
    _progress(0.5)

    # Stage 5: Draw route
    loop = bool(trip.get("loop_route", 0))
    canvas = draw_route(
        canvas, stops, zoom, origin_px, origin_py,
        route_color=style.route_color,
        shadow_color=style.route_shadow_color,
        line_weight=max(2.0, 3.0 * scale),
        loop=loop,
    )
    _progress(0.6)

    # Stage 6: Composite photos
    canvas = composite_photos(
        canvas, stops, zoom, origin_px, origin_py,
        data_dir=data_dir,
        trip_id=trip["id"],
        photo_diameter=max(60, int(80 * scale)),
        marker_color=style.marker_color,
        photo_border_color=style.photo_border_color,
        marker_size=max(12, int(16 * scale)),
        border_width=max(3, int(4 * scale)),
    )
    _progress(0.7)

    # Stage 7: Place labels
    canvas = place_labels(
        canvas, stops, zoom, origin_px, origin_py,
        text_color=style.label_text_color,
        accent_color=style.label_accent_color,
        bg_color=style.label_bg_color,
        city_font_size=max(14, int(18 * scale)),
        dates_font_size=max(11, int(14 * scale)),
    )
    _progress(0.8)

    # Stage 8: Title banner
    show_title = trip.get("show_title", 1)
    if show_title:
        canvas = render_title_banner(
            canvas,
            trip.get("title", ""),
            trip.get("subtitle", ""),
            banner_bg=style.banner_bg_color,
            text_color=style.banner_text_color,
            title_font_size=max(24, int(48 * scale)),
            subtitle_font_size=max(14, int(24 * scale)),
        )
    _progress(0.9)

    # Stage 9: Flatten and save
    output_dir = Path(data_dir) / "trips" / trip["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    output_path = output_dir / f"travel_map_{style_name}.png"

    rgb = canvas.convert("RGB")
    rgb.save(str(output_path), "PNG", dpi=(dpi, dpi))
    _progress(1.0)

    return output_path


async def generate_preview(
    trip: dict,
    stops: list[dict],
    style_name: str = "watercolor",
    api_key: str = "",
    data_dir: str = "/data",
) -> Path:
    """Generate a low-res preview (1200px wide)."""
    # Override print settings for preview
    preview_trip = dict(trip)
    aspect = trip.get("print_height", 18.0) / trip.get("print_width", 24.0)
    preview_trip["dpi"] = 1  # hack: use 1 DPI with pixel-based dimensions
    preview_trip["print_width"] = 1200
    preview_trip["print_height"] = int(1200 * aspect)

    output_dir = Path(data_dir) / "trips" / trip["id"] / "output"
    output_dir.mkdir(parents=True, exist_ok=True)
    preview_path = output_dir / "preview.png"

    style = get_style(style_name)

    canvas, zoom, origin_px, origin_py = await fetch_and_stitch_tiles(
        stops=stops,
        canvas_width=int(preview_trip["print_width"]),
        canvas_height=int(preview_trip["print_height"]),
        url_template=style.url_template,
        api_key=api_key,
    )

    loop = bool(trip.get("loop_route", 0))
    canvas = draw_route(
        canvas, stops, zoom, origin_px, origin_py,
        route_color=style.route_color,
        shadow_color=style.route_shadow_color,
        line_weight=2.0,
        loop=loop,
    )

    canvas = composite_photos(
        canvas, stops, zoom, origin_px, origin_py,
        data_dir=data_dir,
        trip_id=trip["id"],
        photo_diameter=40,
        marker_color=style.marker_color,
        photo_border_color=style.photo_border_color,
    )

    canvas = place_labels(
        canvas, stops, zoom, origin_px, origin_py,
        text_color=style.label_text_color,
        accent_color=style.label_accent_color,
        bg_color=style.label_bg_color,
        city_font_size=12,
        dates_font_size=10,
    )

    if trip.get("show_title", 1):
        canvas = render_title_banner(
            canvas,
            trip.get("title", ""),
            trip.get("subtitle", ""),
            banner_bg=style.banner_bg_color,
            text_color=style.banner_text_color,
            title_font_size=24,
            subtitle_font_size=14,
        )

    rgb = canvas.convert("RGB")
    rgb.save(str(preview_path), "PNG")
    return preview_path
