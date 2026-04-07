from pathlib import Path

from PIL import Image

from app.config import settings


def _photos_dir(trip_id: str) -> Path:
    d = Path(settings.data_dir) / "trips" / trip_id / "photos"
    d.mkdir(parents=True, exist_ok=True)
    return d


async def save_photo(trip_id: str, stop_id: str, file_data: bytes) -> str:
    from io import BytesIO

    # Decode whatever format was uploaded and normalise to JPEG.
    # This handles WebP, PNG, HEIC, etc. transparently.
    img = Image.open(BytesIO(file_data))
    img = img.convert("RGB")  # drop alpha, ensure JPEG-compatible mode

    photos = _photos_dir(trip_id)
    original = photos / f"{stop_id}_original.jpg"
    img.save(original, "JPEG", quality=92)

    # Generate thumbnail
    thumb = photos / f"{stop_id}_thumb.jpg"
    img.thumbnail((256, 256))
    img.save(thumb, "JPEG", quality=85)

    return f"{stop_id}_original.jpg"


async def delete_photo(trip_id: str, stop_id: str) -> None:
    photos = _photos_dir(trip_id)
    for suffix in ("_original.jpg", "_thumb.jpg"):
        path = photos / f"{stop_id}{suffix}"
        if path.exists():
            path.unlink()


def get_photo_path(trip_id: str, stop_id: str, thumbnail: bool = False) -> Path | None:
    photos = Path(settings.data_dir) / "trips" / trip_id / "photos"
    suffix = "_thumb.jpg" if thumbnail else "_original.jpg"
    path = photos / f"{stop_id}{suffix}"
    return path if path.exists() else None
