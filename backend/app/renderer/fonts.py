from pathlib import Path
from functools import lru_cache

from PIL import ImageFont

FONTS_DIR = Path(__file__).parent.parent / "fonts"


@lru_cache(maxsize=32)
def get_title_font(size: int) -> ImageFont.FreeTypeFont:
    path = FONTS_DIR / "PlayfairDisplay-Bold.ttf"
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)


@lru_cache(maxsize=32)
def get_body_font(size: int) -> ImageFont.FreeTypeFont:
    path = FONTS_DIR / "SourceSans3-Regular.ttf"
    if not path.exists():
        return ImageFont.load_default()
    return ImageFont.truetype(str(path), size)
