import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, HTTPException, Depends, UploadFile, File
from fastapi.responses import FileResponse

import aiosqlite

from app.database import get_db
from app.models import StopCreate, StopUpdate, StopReorder, Stop
from app.services import photo_service, geocode_service
from app.config import settings

router = APIRouter(prefix="/trips/{trip_id}/stops", tags=["stops"])


async def _get_db():
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


async def _verify_trip(db: aiosqlite.Connection, trip_id: str):
    cursor = await db.execute("SELECT id FROM trips WHERE id = ?", (trip_id,))
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Trip not found")


@router.post("", response_model=Stop, status_code=201)
async def add_stop(
    trip_id: str, body: StopCreate, db: aiosqlite.Connection = Depends(_get_db)
):
    await _verify_trip(db, trip_id)

    lat, lon = body.lat, body.lon
    if lat is None or lon is None:
        results = await geocode_service.geocode(body.city)
        if not results:
            raise HTTPException(
                status_code=400,
                detail=f"Could not geocode city: {body.city}. Provide lat/lon manually.",
            )
        lat, lon = results[0]["lat"], results[0]["lon"]

    # Get next sort_order
    cursor = await db.execute(
        "SELECT COALESCE(MAX(sort_order), -1) + 1 FROM stops WHERE trip_id = ?",
        (trip_id,),
    )
    row = await cursor.fetchone()
    sort_order = row[0]

    stop_id = str(uuid.uuid4())
    now = _now()
    await db.execute(
        """INSERT INTO stops (id, trip_id, sort_order, city, label, lat, lon,
           dates, nights, highlight, created_at)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            stop_id, trip_id, sort_order, body.city, body.label,
            lat, lon, body.dates, body.nights, int(body.highlight), now,
        ),
    )
    await db.execute("UPDATE trips SET updated_at = ? WHERE id = ?", (_now(), trip_id))
    await db.commit()

    cursor = await db.execute("SELECT * FROM stops WHERE id = ?", (stop_id,))
    stop = dict(await cursor.fetchone())
    stop["highlight"] = bool(stop["highlight"])
    return stop


@router.put("/reorder", response_model=list[Stop])
async def reorder_stops(
    trip_id: str, body: StopReorder, db: aiosqlite.Connection = Depends(_get_db)
):
    await _verify_trip(db, trip_id)
    for i, sid in enumerate(body.stop_ids):
        await db.execute(
            "UPDATE stops SET sort_order = ? WHERE id = ? AND trip_id = ?",
            (i, sid, trip_id),
        )
    await db.execute("UPDATE trips SET updated_at = ? WHERE id = ?", (_now(), trip_id))
    await db.commit()

    cursor = await db.execute(
        "SELECT * FROM stops WHERE trip_id = ? ORDER BY sort_order", (trip_id,)
    )
    rows = await cursor.fetchall()
    stops = [dict(r) for r in rows]
    for s in stops:
        s["highlight"] = bool(s["highlight"])
    return stops


@router.put("/{stop_id}", response_model=Stop)
async def update_stop(
    trip_id: str, stop_id: str, body: StopUpdate,
    db: aiosqlite.Connection = Depends(_get_db),
):
    await _verify_trip(db, trip_id)
    cursor = await db.execute(
        "SELECT * FROM stops WHERE id = ? AND trip_id = ?", (stop_id, trip_id)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Stop not found")

    updates = body.model_dump(exclude_none=True)
    if updates:
        if "highlight" in updates:
            updates["highlight"] = int(updates["highlight"])
        fields = [f"{k} = ?" for k in updates]
        values = list(updates.values()) + [stop_id]
        await db.execute(f"UPDATE stops SET {', '.join(fields)} WHERE id = ?", values)
        await db.execute("UPDATE trips SET updated_at = ? WHERE id = ?", (_now(), trip_id))
        await db.commit()

    cursor = await db.execute("SELECT * FROM stops WHERE id = ?", (stop_id,))
    stop = dict(await cursor.fetchone())
    stop["highlight"] = bool(stop["highlight"])
    return stop


@router.delete("/{stop_id}", status_code=204)
async def delete_stop(
    trip_id: str, stop_id: str, db: aiosqlite.Connection = Depends(_get_db)
):
    await _verify_trip(db, trip_id)
    cursor = await db.execute(
        "SELECT * FROM stops WHERE id = ? AND trip_id = ?", (stop_id, trip_id)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Stop not found")

    await photo_service.delete_photo(trip_id, stop_id)
    await db.execute("DELETE FROM stops WHERE id = ?", (stop_id,))
    await db.execute("UPDATE trips SET updated_at = ? WHERE id = ?", (_now(), trip_id))
    await db.commit()


@router.post("/{stop_id}/photo", response_model=Stop)
async def upload_photo(
    trip_id: str, stop_id: str,
    file: UploadFile = File(...),
    db: aiosqlite.Connection = Depends(_get_db),
):
    await _verify_trip(db, trip_id)
    cursor = await db.execute(
        "SELECT * FROM stops WHERE id = ? AND trip_id = ?", (stop_id, trip_id)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Stop not found")

    ACCEPTED_TYPES = {
        "image/jpeg", "image/png", "image/webp", "image/gif",
        "image/heic", "image/heif", "image/tiff", "image/bmp",
    }
    if file.content_type and file.content_type.lower() not in ACCEPTED_TYPES:
        raise HTTPException(status_code=415, detail=f"Unsupported image type: {file.content_type}")

    data = await file.read()
    max_bytes = settings.max_upload_mb * 1024 * 1024
    if len(data) > max_bytes:
        raise HTTPException(status_code=413, detail=f"File exceeds {settings.max_upload_mb}MB limit")

    photo_path = await photo_service.save_photo(trip_id, stop_id, data)
    await db.execute(
        "UPDATE stops SET photo_path = ? WHERE id = ?", (photo_path, stop_id)
    )
    await db.commit()

    cursor = await db.execute("SELECT * FROM stops WHERE id = ?", (stop_id,))
    stop = dict(await cursor.fetchone())
    stop["highlight"] = bool(stop["highlight"])
    return stop


@router.delete("/{stop_id}/photo", status_code=204)
async def delete_photo(
    trip_id: str, stop_id: str, db: aiosqlite.Connection = Depends(_get_db)
):
    await _verify_trip(db, trip_id)
    cursor = await db.execute(
        "SELECT * FROM stops WHERE id = ? AND trip_id = ?", (stop_id, trip_id)
    )
    if await cursor.fetchone() is None:
        raise HTTPException(status_code=404, detail="Stop not found")

    await photo_service.delete_photo(trip_id, stop_id)
    await db.execute("UPDATE stops SET photo_path = NULL WHERE id = ?", (stop_id,))
    await db.commit()


@router.get("/{stop_id}/photo/thumb")
async def get_photo_thumbnail(trip_id: str, stop_id: str):
    path = photo_service.get_photo_path(trip_id, stop_id, thumbnail=True)
    if path is None:
        raise HTTPException(status_code=404, detail="Thumbnail not found")
    return FileResponse(str(path), media_type="image/jpeg")
