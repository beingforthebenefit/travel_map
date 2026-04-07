from fastapi import APIRouter, HTTPException, Depends, UploadFile, File

import aiosqlite

from app.database import get_db
from app.models import (
    TripCreate, TripUpdate, Trip, TripSummary, TripDetail,
)
from app.services import trip_service

router = APIRouter(prefix="/trips", tags=["trips"])


async def _get_db():
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


@router.get("", response_model=list[TripSummary])
async def list_trips(db: aiosqlite.Connection = Depends(_get_db)):
    return await trip_service.list_trips(db)


@router.post("", response_model=TripDetail, status_code=201)
async def create_trip(body: TripCreate, db: aiosqlite.Connection = Depends(_get_db)):
    trip = await trip_service.create_trip(db, body.title, body.subtitle)
    trip["stops"] = []
    trip["show_title"] = bool(trip["show_title"])
    return trip


@router.get("/{trip_id}", response_model=TripDetail)
async def get_trip(trip_id: str, db: aiosqlite.Connection = Depends(_get_db)):
    trip = await trip_service.get_trip_with_stops(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip["show_title"] = bool(trip["show_title"])
    for s in trip["stops"]:
        s["highlight"] = bool(s["highlight"])
    return trip


@router.put("/{trip_id}", response_model=Trip)
async def update_trip(
    trip_id: str, body: TripUpdate, db: aiosqlite.Connection = Depends(_get_db)
):
    updates = body.model_dump(exclude_none=True)
    trip = await trip_service.update_trip(db, trip_id, updates)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip["show_title"] = bool(trip["show_title"])
    return trip


@router.delete("/{trip_id}", status_code=204)
async def delete_trip(trip_id: str, db: aiosqlite.Connection = Depends(_get_db)):
    deleted = await trip_service.delete_trip(db, trip_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Trip not found")


@router.post("/{trip_id}/duplicate", response_model=TripDetail, status_code=201)
async def duplicate_trip(trip_id: str, db: aiosqlite.Connection = Depends(_get_db)):
    trip = await trip_service.duplicate_trip(db, trip_id)
    if trip is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    trip["show_title"] = bool(trip["show_title"])
    for s in trip["stops"]:
        s["highlight"] = bool(s["highlight"])
    return trip


@router.post("/import", response_model=TripDetail, status_code=201)
async def import_trip(file: UploadFile = File(...), db: aiosqlite.Connection = Depends(_get_db)):
    content = await file.read()
    trip = await trip_service.import_trip_yaml(db, content.decode("utf-8"))
    trip["show_title"] = bool(trip["show_title"])
    for s in trip["stops"]:
        s["highlight"] = bool(s["highlight"])
    return trip


@router.get("/{trip_id}/export")
async def export_trip(trip_id: str, db: aiosqlite.Connection = Depends(_get_db)):
    from fastapi.responses import Response
    yaml_str = await trip_service.export_trip_yaml(db, trip_id)
    if yaml_str is None:
        raise HTTPException(status_code=404, detail="Trip not found")
    return Response(
        content=yaml_str,
        media_type="application/x-yaml",
        headers={"Content-Disposition": f"attachment; filename={trip_id}.yaml"},
    )
