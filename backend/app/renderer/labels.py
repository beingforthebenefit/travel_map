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
    min_y: int = 0  # label cannot be pushed above this y coordinate


def render_label(
    city: str,
    dates: str,
    city_font_size: int = 18,
    dates_font_size: int = 14,
    text_color: tuple[int, int, int] = (30, 30, 30),
    accent_color: tuple[int, int, int] = (139, 69, 19),
    bg_color: tuple[int, int, int, int] = (255, 255, 255, 200),
) -> Image.Image:
    """Render a city label with name and dates on a semi-transparent background pill."""
    city_font = get_title_font(city_font_size)
    dates_font = get_body_font(dates_font_size)
    # Scale padding with font size so labels look right at high DPI
    padding = max(8, city_font_size // 2)

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
    radius = min(max(12, city_font_size // 2), label_h // 3)

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


def _overlaps(a: LabelBox, b: LabelBox, pad: int = 4) -> bool:
    return (a.x - pad < b.x + b.width and a.x + a.width + pad > b.x and
            a.y - pad < b.y + b.height and a.y + a.height + pad > b.y)


def collision_avoidance(boxes: list[LabelBox], iterations: int = 12, pad: int = 8):
    """Nudge overlapping labels apart bidirectionally, respecting each label's min_y floor."""
    for _ in range(iterations):
        moved = False
        for i in range(len(boxes)):
            for j in range(i + 1, len(boxes)):
                a, b = boxes[i], boxes[j]
                if not _overlaps(a, b, pad):
                    continue
                # Compute vertical overlap amount
                overlap_y = min(a.y + a.height, b.y + b.height) - max(a.y, b.y) + pad
                if overlap_y > 0:
                    # Push apart in both directions (half each), but respect min_y
                    shift = (overlap_y + 1) // 2
                    new_ay = a.y - shift
                    if new_ay < a.min_y:
                        # a can't go up — push b down by the full amount instead
                        b.y += overlap_y
                    else:
                        a.y = new_ay
                        b.y += shift
                    moved = True
        if not moved:
            break


def _label_candidates(
    cx: int, cy: int,
    lw: int, lh: int,
    gap: int,
    has_photo: bool,
    photo_diameter: int,
) -> list[tuple[int, int]]:
    """Return (lx, ly) candidate positions in preference order.

    For stops with photos (bubble above marker), the bubble occupies the space
    above cy, so we prefer placing the label beside the bubble first.
    For dot stops we prefer below, then sides.
    """
    if has_photo:
        photo_gap = max(8, photo_diameter // 10)
        r = photo_diameter // 2
        # Vertical centre of the bubble
        bubble_cy = cy - r - photo_gap
        bubble_top = cy - photo_diameter - photo_gap
        bubble_bottom = cy - photo_gap

        return [
            # Beside the bubble (vertically centred on it)
            (cx + r + gap,          bubble_cy - lh // 2),   # E of bubble
            (cx - r - gap - lw,     bubble_cy - lh // 2),   # W of bubble
            # Beside the bubble, top-aligned with bubble
            (cx + r + gap,          bubble_top),             # E of bubble, top
            (cx - r - gap - lw,     bubble_top),             # W of bubble, top
            # Beside the bubble, bottom-aligned with bubble
            (cx + r + gap,          bubble_bottom - lh),     # E of bubble, bottom
            (cx - r - gap - lw,     bubble_bottom - lh),     # W of bubble, bottom
            # Between bubble bottom and marker
            (cx - lw // 2,          bubble_bottom + 2),      # S of bubble
            # Above bubble
            (cx - lw // 2,          bubble_top - lh - 4),    # N of bubble
            # Below marker (last resort)
            (cx - lw // 2,          cy + gap),               # S of marker
        ]
    else:
        return [
            (cx - lw // 2,     cy + gap),            # S
            (cx + gap,         cy - lh // 2),        # E
            (cx - lw - gap,    cy - lh // 2),        # W
            (cx - lw // 2,     cy - lh - gap),       # N
            (cx + gap,         cy),                  # SE
            (cx - lw - gap,    cy),                  # SW
            (cx + gap,         cy - lh),             # NE
            (cx - lw - gap,    cy - lh),             # NW
        ]


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
    photo_diameter: int = 80,
) -> Image.Image:
    """Place city labels with greedy candidate placement + light collision avoidance.

    Greedy pass: for each stop, try candidate positions in preference order and
    pick the first that doesn't overlap already-placed labels or photo bubbles.
    A light collision-avoidance pass then resolves any remaining overlaps.
    """
    result = canvas.copy()
    bg_with_opacity = (bg_color[0], bg_color[1], bg_color[2], int(255 * bg_opacity))
    cw, ch = canvas.size
    gap = max(14, city_font_size)

    # Pre-compute stop canvas positions
    positions: list[tuple[int, int]] = []
    for stop in stops:
        px, py = lat_lon_to_pixel(stop["lat"], stop["lon"], zoom)
        positions.append((int(px - origin_px), int(py - origin_py)))

    # Build fixed obstacle boxes for photo bubbles (not moveable)
    photo_gap = max(8, photo_diameter // 10)
    obstacles: list[LabelBox] = []
    for i, stop in enumerate(stops):
        if stop.get("photo_path"):
            cx, cy = positions[i]
            r = photo_diameter // 2
            obstacles.append(LabelBox(
                x=cx - r, y=cy - photo_diameter - photo_gap,
                width=photo_diameter, height=photo_diameter + photo_gap,
                stop_index=-1,
            ))

    # Greedy label placement
    placed_boxes: list[LabelBox] = []
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
        lw, lh = label_img.size
        cx, cy = positions[i]
        has_photo = bool(stop.get("photo_path"))

        all_obstacles = obstacles + placed_boxes
        chosen: tuple[int, int] | None = None

        for lx, ly in _label_candidates(cx, cy, lw, lh, gap, has_photo, photo_diameter):
            # Skip if entirely off-canvas
            if lx + lw <= 0 or lx >= cw or ly + lh <= 0 or ly >= ch:
                continue
            candidate = LabelBox(x=lx, y=ly, width=lw, height=lh, stop_index=i)
            if not any(_overlaps(candidate, obs, pad=4) for obs in all_obstacles):
                chosen = (lx, ly)
                break

        if chosen is None:
            # Fallback: use first candidate regardless of overlaps
            cands = _label_candidates(cx, cy, lw, lh, gap, has_photo, photo_diameter)
            chosen = cands[0]

        lx, ly = chosen
        box = LabelBox(x=lx, y=ly, width=lw, height=lh, stop_index=i,
                       min_y=cy if has_photo else 0)
        placed_boxes.append(box)
        labels.append((label_img, box))

    # Light collision avoidance pass for any remaining label-label overlaps
    collision_avoidance(placed_boxes, iterations=6, pad=max(4, city_font_size // 4))

    for label_img, box in labels:
        result.paste(label_img, (box.x, box.y), label_img)

    return result


def compute_banner_height(
    title: str,
    subtitle: str = "",
    title_font_size: int = 48,
    subtitle_font_size: int = 24,
) -> int:
    """Compute the pixel height of the title banner without rendering it."""
    title_font = get_title_font(title_font_size)
    subtitle_font = get_body_font(subtitle_font_size)
    temp = Image.new("RGBA", (1, 1))
    draw = ImageDraw.Draw(temp)
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_h = title_bbox[3] - title_bbox[1]
    sub_h = 0
    if subtitle:
        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_h = sub_bbox[3] - sub_bbox[1]
    v_pad = max(16, title_font_size // 3)
    gap = max(12, title_font_size // 4)
    return title_h + sub_h + v_pad * 2 + gap


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

    v_pad = max(16, title_font_size // 3)
    gap = max(12, title_font_size // 4)
    banner_h = title_h + sub_h + v_pad * 2 + gap
    banner = Image.new("RGBA", (w, banner_h), banner_bg)
    draw = ImageDraw.Draw(banner)

    # Title centered
    title_bbox = draw.textbbox((0, 0), title, font=title_font)
    title_w = title_bbox[2] - title_bbox[0]
    draw.text(
        ((w - title_w) // 2, v_pad),
        title, font=title_font, fill=(*text_color, 255),
    )

    if subtitle:
        sub_bbox = draw.textbbox((0, 0), subtitle, font=subtitle_font)
        sub_w = sub_bbox[2] - sub_bbox[0]
        draw.text(
            ((w - sub_w) // 2, v_pad + title_h + gap),
            subtitle, font=subtitle_font, fill=(*text_color, 180),
        )

    result.paste(banner, (0, 0), banner)
    return result
