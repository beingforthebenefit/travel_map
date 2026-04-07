from fastapi import APIRouter, Query

from app.models import GeocodeResult
from app.services import geocode_service

router = APIRouter(tags=["geocode"])


@router.get("/geocode", response_model=list[GeocodeResult])
async def geocode(q: str = Query(..., min_length=1)):
    return await geocode_service.geocode(q)
