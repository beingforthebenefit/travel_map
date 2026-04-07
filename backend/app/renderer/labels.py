from dataclasses import dataclass

from PIL import Image, ImageDraw

from app.renderer.fonts import get_title_font, get_body_font
from app.renderer.tiles import lat_lon_to_pixel


@dataclass
class LabelBox:
    x: int
    y: int
    width: int
    height: int
    stop_index: int


def render_label(
    city: str,
    dates: str,
    city_font_size: int = 18,
    dates_font_size: int = 14,
    text_color: tuple[int, int, int] = (30, 30, 30),
    accent_color: tuple[int, int, int] = (139, 69, 19),
    bg_color: tuple[int, int, int, int] = (255, 255, 255, 200),
    padding: int = 8,
) -> Image.Image:
    """Render a city label with name and dates on a semi-transparent background pill."""
    city_font = get_title_font(city_font_size)
    dates_font = get_body_font(dates_font_size)

    # Measure text
    temp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp)
    city_bbox = draw.textbbox((0, 0), city, font=city_font)
    city_w = city_bbox[2] - city_bbox[0]
    city_h = city_bbox[3] - city_bbox[1]

    dates_bbox = draw.textbbox((0, 0), dates, font=dates_font)
    dates_w = dates_bbox[2] - dates_bbox[0]
    dates_h = dates_bbox[3] - dates_bbox[1]

    label_w = max(city_w, dates_w) + padding * 2
    label_h = city_h + dates_h + padding * 3
    radius = min(12, label_h // 3)

    # Create label image
    label = Image.new("RGBA", (label_w, label_h), (0, 0, 0, 0))
    draw = ImageDraw.Draw(label)

    # Rounded rectangle background
    draw.rounded_rectangle(
        (0, 0, label_w - 1, label_h - 1),
        radius=radius,
        fill=bg_color,
    )

    # City name
    city_x = (label_w - city_w) // 2
    draw.text((city_x, padding), city, font=city_font, fill=(*text_color, 255))

    # Dates
    dates_x = (label_w - dates_w) // 2
    draw.text(
        (dates_x, padding + city_h + padding // 2),
        dates, font=dates_font, fill=(*accent_color, 255),
    )

    return label


def collision_avoidance(boxes: list[LabelBox], iterations: int = 3, pad: int = 8):
    """Nudge overlapping labels apart vertically."""
    for _ in range(iterations):
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                # Check overlap
                if (a.x < b.x + b.width and a.x + a.width > b.x and
                        a.y < b.y + b.height and a.y + a.height > b.y):
                    overlap = (a.y + a.height) - b.y + pad
                    if overlap > 0:
                        b.y += overlap


def place_labels(
    canvas: Image.Image,
    stops: list[dict],
    zoom: int,
    origin_px: float,
    origin_py: float,
    text_color: tuple[int, int, int] = (30, 30, 30),
    accent_color: tuple[int, int, int] = (139, 69, 19),
    bg_color: tuple[int, int, int, int] = (255, 255, 255, 200),
    city_font_size: int = 18,
    dates_font_size: int = 14,
    bg_opacity: float = 0.78,
) -> Image.Image:
    """Place city labels on the canvas with collision avoidance."""
    result = canvas.copy()
    bg_with_opacity = (bg_color[0], bg_color[1], bg_color[2], int(255 * bg_opacity))

    # Render all labels and compute positions
    labels: list[tuple[Image.Image, LabelBox]] = []
    for i, stop in enumerate(stops):
        display_name = stop.get("label") or stop["city"]
        label_img = render_label(
            display_name, stop["dates"],
            city_font_size=city_font_size,
            dates_font_size=dates_font_size,
            text_color=text_color,
            accent_color=accent_color,
            bg_color=bg_with_opacity,
        )
        px, py = lat_lon_to_pixel(stop["lat"], stop["lon"], zoom)
        cx = int(px - origin_px)
        cy = int(py - origin_py)

        # Default: label below marker
        lx = cx - label_img.width // 2
        ly = cy + 20  # offset below marker

        box = LabelBox(x=lx, y=ly, width=label_img.width, height=label_img.height, stop_index=i)
        labels.append((label_img, box))

    # Run collision avoidance
    boxes = [b for _, b in labels]
    collision_avoidance(boxes)

    # Paste labels
    for label_img, box in labels:
        result.paste(label_img, (box.x, box.y), label_img)

    return result


def render_title_banner(
    canvas: Image.Image,
    title: str,
    subtitle: str = "",
    banner_bg: tuple[int, int, int, int] = (255, 255, 255, 180),
    text_color: tuple[int, int, int] = (30, 30, 30),
    title_font_size: int = 48,
    subtitle_font_size: int = 24,
) -> Image.Image:
    """Render a semi-transparent title banner at the top of the canvas."""
    result = canvas.copy()
    w = canvas.width

    title_font = get_title_font(title_font_size)
    subtitle_font = get_body_font(subtitle_font_size)

    # Measure
    temp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]

    sub_h = 0
    if subtitle:
        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_h = sub_bbox[3] - sub_bbox[1]

    banner_h = title_h + sub_h + 60  # padding
    banner = Image.new("RGBA", (w, banner_h), banner_bg)
    draw = ImageDraw.Draw(banner)

    # Title centered
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(
        ((w - title_w) // 2, 16),
        title, font=title_font, fill=(*text_color, 255),
    )

    if subtitle:
        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text(
            ((w - sub_w) // 2, 16 + title_h + 12),
            subtitle, font=subtitle_font, fill=(*text_color, 180),
        )

    result.paste(banner, (0, 0), banner)
    return result
