from pathlib import Path

from PIL import Image, ImageDraw

from app.renderer.tiles import lat_lon_to_pixel


def create_photo_bubble(
    photo_path: str,
    diameter: int = 80,
    border_color: tuple[int, int, int] = (255, 255, 255),
    border_width: int = 4,
) -> Image.Image:
    """Create a circular photo bubble with a border ring."""
    img = Image.open(photo_path).convert("RGBA")

    # Crop to square
    size = min(img.size)
    left = (img.width - size) // 2
    top = (img.height - size) // 2
    img = img.crop((left, top, left + size, top + size))
    img = img.resize((diameter, diameter), Image.LANCZOS)

    # Create circular mask
    mask = Image.new("L", (diameter, diameter), 0)
    draw = ImageDraw.Draw(mask)
    draw.ellipse((0, 0, diameter - 1, diameter - 1), fill=255)

    # Apply mask
    result = Image.new("RGBA", (diameter, diameter), (0, 0, 0, 0))
    result.paste(img, (0, 0), mask)

    # Draw border ring
    if border_width > 0:
        border_draw = ImageDraw.Draw(result)
        for i in range(border_width):
            border_draw.ellipse(
                (i, i, diameter - 1 - i, diameter - 1 - i),
                outline=(*border_color, 255),
            )

    return result


def draw_marker_dot(
    color: tuple[int, int, int] = (139, 69, 19),
    size: int = 16,
    border_color: tuple[int, int, int] = (255, 255, 255),
    border_width: int = 2,
) -> Image.Image:
    """Draw a simple dot marker for stops without photos."""
    total = size + border_width * 2
    img = Image.new("RGBA", (total, total), (0, 0, 0, 0))
    draw = ImageDraw.Draw(img)

    # Border circle
    draw.ellipse(
        (0, 0, total - 1, total - 1),
        fill=(*border_color, 255),
    )
    # Inner circle
    draw.ellipse(
        (border_width, border_width, total - 1 - border_width, total - 1 - border_width),
        fill=(*color, 255),
    )
    return img


def composite_photos(
    canvas: Image.Image,
    stops: list[dict],
    zoom: int,
    origin_px: float,
    origin_py: float,
    data_dir: str,
    trip_id: str,
    photo_diameter: int = 80,
    marker_color: tuple[int, int, int] = (139, 69, 19),
    photo_border_color: tuple[int, int, int] = (255, 255, 255),
) -> Image.Image:
    """Composite photo bubbles or dot markers onto the canvas."""
    result = canvas.copy()

    for stop in stops:
        px, py = lat_lon_to_pixel(stop["lat"], stop["lon"], zoom)
        cx = int(px - origin_px)
        cy = int(py - origin_py)

        if stop.get("photo_path"):
            photo_file = Path(data_dir) / "trips" / trip_id / "photos" / stop["photo_path"]
            if photo_file.exists():
                bubble = create_photo_bubble(
                    str(photo_file),
                    diameter=photo_diameter,
                    border_color=photo_border_color,
                )
                # Position bubble above the stop point
                paste_x = cx - bubble.width // 2
                paste_y = cy - bubble.height - 8
                result.paste(bubble, (paste_x, paste_y), bubble)
                continue

        # No photo — draw a dot marker
        dot = draw_marker_dot(color=marker_color, size=16)
        paste_x = cx - dot.width // 2
        paste_y = cy - dot.height // 2
        result.paste(dot, (paste_x, paste_y), dot)

    return result
