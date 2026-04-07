import pytest
import tempfile
from pathlib import Path
from PIL import Image
from app.renderer.photos import create_photo_bubble, draw_marker_dot


def test_photo_bubble_circular():
    """Circular crop should have transparent corners."""
    with tempfile.NamedTemporaryFile(suffix=".jpg", delete=False) as f:
        img = Image.new("RGB", (200, 200), "red")
        img.save(f.name, "JPEG")
        bubble = create_photo_bubble(f.name, diameter=80)

    assert bubble.size == (80, 80)
    assert bubble.mode == "RGBA"
    # Corner pixel should be transparent
    assert bubble.getpixel((0, 0))[3] == 0
    # Center pixel should be opaque
    assert bubble.getpixel((40, 40))[3] == 255


def test_marker_dot_size():
    dot = draw_marker_dot(size=16, border_width=2)
    assert dot.size == (20, 20)  # 16 + 2*2
    assert dot.mode == "RGBA"
    # Center should be opaque
    cx, cy = dot.width // 2, dot.height // 2
    assert dot.getpixel((cx, cy))[3] == 255
    # Corner should be transparent
    assert dot.getpixel((0, 0))[3] == 0
