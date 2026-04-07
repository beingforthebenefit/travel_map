import math
from pathlib import Path
from typing import Callable

from PIL import Image

from app.renderer.tiles import fetch_and_stitch_tiles
from app.renderer.route import draw_route
from app.renderer.photos import composite_photos
from app.renderer.labels import place_labels, render_title_banner, compute_banner_height
from app.renderer.styles import get_style
from app.services.routing_service import fetch_road_waypoints


def _geo_distance_km(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Approximate great-circle distance in kilometres."""
    dlat = math.radians(lat2 - lat1)
    dlon = math.radians(lon2 - lon1)
    a = (math.sin(dlat / 2) ** 2
         + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(dlon / 2) ** 2)
    return 6371 * 2 * math.asin(math.sqrt(a))


def _merge_nearby_stops(stops: list[dict], threshold_km: float = 40.0) -> list[dict]:
    """Merge consecutive stops that are geographically very close into a single map point.

    The merged point gets a combined city name ("Lisbon & Sintra"), combined dates,
    the average lat/lon, and inherits the photo/highlight from the group.
    """
    if len(stops) < 2:
        return stops

    merged: list[dict] = []
    i = 0
    while i < len(stops):
        group = [i]
        j = i + 1
        while j < len(stops):
            last = group[-1]
            dist = _geo_distance_km(
                stops[last]["lat"], stops[last]["lon"],
                stops[j]["lat"], stops[j]["lon"],
            )
            if dist < threshold_km:
                group.append(j)
                j += 1
            else:
                break

        if len(group) == 1:
            merged.append(stops[i])
        else:
            grp = [stops[k] for k in group]
            city_names = " & ".join(s.get("label") or s["city"] for s in grp)
            dates = " / ".join(s["dates"] for s in grp)
            avg_lat = sum(s["lat"] for s in grp) / len(grp)
            avg_lon = sum(s["lon"] for s in grp) / len(grp)
            highlight = any(s.get("highlight") for s in grp)
            photo = next((s.get("photo_path") for s in grp if s.get("photo_path")), None)
            merged.append({
                **grp[0],
                "label": city_names,
                "dates": dates,
                "lat": avg_lat,
                "lon": avg_lon,
                "highlight": highlight,
                "photo_path": photo,
            })

        i = group[-1] + 1

    return merged


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

    # Compute banner height upfront so tiles can be shifted to avoid overlap
    title_font_size = max(24, int(48 * scale))
    subtitle_font_size = max(14, int(24 * scale))
    show_title = trip.get("show_title", 1)
    top_margin = 0
    if show_title:
        top_margin = compute_banner_height(
            trip.get("title", ""),
            trip.get("subtitle", ""),
            title_font_size=title_font_size,
            subtitle_font_size=subtitle_font_size,
        )

    # Stage 1-4: Fetch and stitch tiles (shifted down to clear the banner)
    _progress(0.0)
    canvas, zoom, origin_px, origin_py = await fetch_and_stitch_tiles(
        stops=stops,
        canvas_width=canvas_width,
        canvas_height=canvas_height,
        url_template=style.url_template,
        api_key=api_key,
        progress_callback=_progress,
        top_margin=top_margin,
    )
    _progress(0.5)

    # Merge consecutive stops that are very close on the map into a single point
    render_stops = _merge_nearby_stops(stops)

    # Stage 5: Draw route
    loop = bool(trip.get("loop_route", 0))
    road_waypoints = None
    if trip.get("route_type") == "roads":
        road_waypoints = await fetch_road_waypoints(render_stops, loop=loop)
    line_weight = max(1.5, 2.0 * scale) if road_waypoints else max(2.0, 3.0 * scale)
    canvas = draw_route(
        canvas, render_stops, zoom, origin_px, origin_py,
        route_color=style.route_color,
        shadow_color=style.route_shadow_color,
        line_weight=line_weight,
        loop=loop,
        waypoints=road_waypoints,
    )
    _progress(0.6)

    # Stage 6: Composite photos
    canvas = composite_photos(
        canvas, render_stops, zoom, origin_px, origin_py,
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
        canvas, render_stops, zoom, origin_px, origin_py,
        text_color=style.label_text_color,
        accent_color=style.label_accent_color,
        bg_color=style.label_bg_color,
        city_font_size=max(14, int(18 * scale)),
        dates_font_size=max(11, int(14 * scale)),
    )
    _progress(0.8)

    # Stage 8: Title banner
    if show_title:
        canvas = render_title_banner(
            canvas,
            trip.get("title", ""),
            trip.get("subtitle", ""),
            banner_bg=style.banner_bg_color,
            text_color=style.banner_text_color,
            title_font_size=title_font_size,
            subtitle_font_size=subtitle_font_size,
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

    show_title = trip.get("show_title", 1)
    prev_title_fs, prev_sub_fs = 24, 14
    top_margin = 0
    if show_title:
        top_margin = compute_banner_height(
            trip.get("title", ""),
            trip.get("subtitle", ""),
            title_font_size=prev_title_fs,
            subtitle_font_size=prev_sub_fs,
        )

    canvas, zoom, origin_px, origin_py = await fetch_and_stitch_tiles(
        stops=stops,
        canvas_width=int(preview_trip["print_width"]),
        canvas_height=int(preview_trip["print_height"]),
        url_template=style.url_template,
        api_key=api_key,
        top_margin=top_margin,
    )

    render_stops = _merge_nearby_stops(stops)

    loop = bool(trip.get("loop_route", 0))
    road_waypoints = None
    if trip.get("route_type") == "roads":
        road_waypoints = await fetch_road_waypoints(render_stops, loop=loop)
    canvas = draw_route(
        canvas, render_stops, zoom, origin_px, origin_py,
        route_color=style.route_color,
        shadow_color=style.route_shadow_color,
        line_weight=1.5 if road_waypoints else 2.0,
        loop=loop,
        waypoints=road_waypoints,
    )

    canvas = composite_photos(
        canvas, render_stops, zoom, origin_px, origin_py,
        data_dir=data_dir,
        trip_id=trip["id"],
        photo_diameter=40,
        marker_color=style.marker_color,
        photo_border_color=style.photo_border_color,
    )

    canvas = place_labels(
        canvas, render_stops, zoom, origin_px, origin_py,
        text_color=style.label_text_color,
        accent_color=style.label_accent_color,
        bg_color=style.label_bg_color,
        city_font_size=12,
        dates_font_size=10,
    )

    if show_title:
        canvas = render_title_banner(
            canvas,
            trip.get("title", ""),
            trip.get("subtitle", ""),
            banner_bg=style.banner_bg_color,
            text_color=style.banner_text_color,
            title_font_size=prev_title_fs,
            subtitle_font_size=prev_sub_fs,
        )

    rgb = canvas.convert("RGB")
    rgb.save(str(preview_path), "PNG")
    return preview_path
