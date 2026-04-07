from pathlib import Path

from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import FileResponse

import aiosqlite

from app.database import get_db
from app.models import RenderRequest, RenderStatus
from app.services import render_service
from app.services.trip_service import get_trip_with_stops
from app.renderer.pipeline import generate_preview
from app.renderer.styles import get_style
from app.config import settings

router = APIRouter(prefix="/trips/{trip_id}/render", tags=["render"])


async def _get_db():
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


@router.post("", status_code=202)
async def start_render(
    trip_id: str,
    body: RenderRequest,
    db: aiosqlite.Connection = Depends(_get_db),
):
    trip = await get_trip_with_stops(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    stops = trip.get("stops", [])
    if not stops:
        raise HTTPException(status_code=400, detail="Trip has no stops")

    # Check if render already in progress
    existing = render_service.get_job(trip_id)
    if existing and existing.status == "rendering":
        raise HTTPException(status_code=409, detail="Render already in progress")

    job_id = await render_service.start_render(
        trip=trip,
        stops=stops,
        style=body.style,
        all_styles=body.all_styles,
    )
    return {"job_id": job_id}


@router.get("/status", response_model=RenderStatus)
async def render_status(trip_id: str):
    job = render_service.get_job(trip_id)
    if job is None:
        return RenderStatus(status="pending")
    return RenderStatus(
        status=job.status,
        progress=job.progress,
        styles_complete=job.styles_complete,
        error=job.error,
    )


@router.get("/{style}.png")
async def download_render(trip_id: str, style: str):
    output = Path(settings.data_dir) / "trips" / trip_id / "output" / f"travel_map_{style}.png"
    if not output.exists():
        raise HTTPException(status_code=404, detail="Render not found")
    return FileResponse(str(output), media_type="image/png", filename=f"travel_map_{style}.png")


@router.get("/preview")
async def preview(
    trip_id: str,
    db: aiosqlite.Connection = Depends(_get_db),
):
    # Check if preview already exists
    preview_path = Path(settings.data_dir) / "trips" / trip_id / "output" / "preview.png"
    if preview_path.exists():
        return FileResponse(str(preview_path), media_type="image/png")

    trip = await get_trip_with_stops(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    stops = trip.get("stops", [])
    if not stops:
        raise HTTPException(status_code=400, detail="Trip has no stops")

    path = await generate_preview(
        trip=trip,
        stops=stops,
        style_name=trip.get("style", "positron"),
        api_key=settings.stadia_api_key,
        data_dir=settings.data_dir,
    )
    return FileResponse(str(path), media_type="image/png")
