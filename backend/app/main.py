from contextlib import asynccontextmanager

from fastapi import FastAPI, APIRouter
from fastapi.middleware.cors import CORSMiddleware

from app.config import settings
from app.database import init_db
from app.routers import trips, stops, geocode, settings as settings_router, render


@asynccontextmanager
async def lifespan(app: FastAPI):
    await init_db()
    yield


app = FastAPI(title="travel_map", version="1.0.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


api = APIRouter(prefix="/api/v1")
api.include_router(trips.router)
api.include_router(stops.router)
api.include_router(geocode.router)
api.include_router(settings_router.router)
api.include_router(render.router)
app.include_router(api)


@app.get("/api/v1/health")
async def health():
    return {"status": "ok"}
