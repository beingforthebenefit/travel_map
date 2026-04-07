from fastapi import APIRouter, Depends

import aiosqlite

from app.database import get_db
from app.models import SettingsResponse, SettingsUpdate

router = APIRouter(tags=["settings"])


async def _get_db():
    db = await get_db()
    try:
        yield db
    finally:
        await db.close()


DEFAULTS = {
    "default_style": "watercolor",
    "default_print_width": "24.0",
    "default_print_height": "18.0",
    "default_dpi": "300",
    "stadia_api_key": "",
}


async def _get_setting(db: aiosqlite.Connection, key: str) -> str:
    cursor = await db.execute("SELECT value FROM settings WHERE key = ?", (key,))
    row = await cursor.fetchone()
    return row["value"] if row else DEFAULTS.get(key, "")


async def _set_setting(db: aiosqlite.Connection, key: str, value: str):
    await db.execute(
        "INSERT INTO settings (key, value) VALUES (?, ?) ON CONFLICT(key) DO UPDATE SET value = ?",
        (key, value, value),
    )


@router.get("/settings", response_model=SettingsResponse)
async def get_settings(db: aiosqlite.Connection = Depends(_get_db)):
    api_key = await _get_setting(db, "stadia_api_key")
    return SettingsResponse(
        stadia_api_key_set=bool(api_key),
        default_style=await _get_setting(db, "default_style"),
        default_print_width=float(await _get_setting(db, "default_print_width")),
        default_print_height=float(await _get_setting(db, "default_print_height")),
        default_dpi=int(await _get_setting(db, "default_dpi")),
    )


@router.put("/settings", response_model=SettingsResponse)
async def update_settings(
    body: SettingsUpdate, db: aiosqlite.Connection = Depends(_get_db)
):
    updates = body.model_dump(exclude_none=True)
    for key, value in updates.items():
        await _set_setting(db, key, str(value))
    await db.commit()
    return await get_settings(db)
