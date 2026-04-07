import uuid
from datetime import datetime, timezone
from pathlib import Path

import aiosqlite
import yaml

from app.config import settings


def _now() -> str:
    return datetime.now(timezone.utc).isoformat()


def _uuid() -> str:
    return str(uuid.uuid4())


async def list_trips(db: aiosqlite.Connection) -> list[dict]:
    cursor = await db.execute(
        """
        SELECT t.id, t.title, t.subtitle, t.updated_at,
               COUNT(s.id) AS stop_count
        FROM trips t
        LEFT JOIN stops s ON s.trip_id = t.id
        GROUP BY t.id
        ORDER BY t.updated_at DESC
        """
    )
    rows = await cursor.fetchall()
    result = []
    for row in rows:
        trip_id = row["id"]
        output_dir = Path(settings.data_dir) / "trips" / trip_id / "output"
        has_output = output_dir.exists() and any(output_dir.glob("*.png"))
        result.append(
            {
                "id": row["id"],
                "title": row["title"],
                "subtitle": row["subtitle"],
                "updated_at": row["updated_at"],
                "stop_count": row["stop_count"],
                "has_output": has_output,
            }
        )
    return result


async def create_trip(db: aiosqlite.Connection, title: str, subtitle: str = "") -> dict:
    trip_id = _uuid()
    now = _now()
    await db.execute(
        "INSERT INTO trips (id, title, subtitle, created_at, updated_at) VALUES (?, ?, ?, ?, ?)",
        (trip_id, title, subtitle, now, now),
    )
    await db.commit()
    return await get_trip(db, trip_id)


async def get_trip(db: aiosqlite.Connection, trip_id: str) -> dict | None:
    cursor = await db.execute("SELECT * FROM trips WHERE id = ?", (trip_id,))
    row = await cursor.fetchone()
    if row is None:
        return None
    return dict(row)


async def get_trip_with_stops(db: aiosqlite.Connection, trip_id: str) -> dict | None:
    trip = await get_trip(db, trip_id)
    if trip is None:
        return None
    cursor = await db.execute(
        "SELECT * FROM stops WHERE trip_id = ? ORDER BY sort_order", (trip_id,)
    )
    rows = await cursor.fetchall()
    trip["stops"] = [dict(r) for r in rows]
    return trip


async def update_trip(db: aiosqlite.Connection, trip_id: str, updates: dict) -> dict | None:
    trip = await get_trip(db, trip_id)
    if trip is None:
        return None
    fields = []
    values = []
    for key, value in updates.items():
        if value is not None:
            if key == "show_title":
                value = int(value)
            fields.append(f"{key} = ?")
            values.append(value)
    if fields:
        fields.append("updated_at = ?")
        values.append(_now())
        values.append(trip_id)
        await db.execute(
            f"UPDATE trips SET {', '.join(fields)} WHERE id = ?", values
        )
        await db.commit()
    return await get_trip(db, trip_id)


async def delete_trip(db: aiosqlite.Connection, trip_id: str) -> bool:
    trip = await get_trip(db, trip_id)
    if trip is None:
        return False
    await db.execute("DELETE FROM trips WHERE id = ?", (trip_id,))
    await db.commit()
    # Clean up files
    trip_dir = Path(settings.data_dir) / "trips" / trip_id
    if trip_dir.exists():
        import shutil
        shutil.rmtree(trip_dir)
    return True


async def duplicate_trip(db: aiosqlite.Connection, trip_id: str) -> dict | None:
    trip = await get_trip_with_stops(db, trip_id)
    if trip is None:
        return None
    new_trip_id = _uuid()
    now = _now()
    await db.execute(
        """INSERT INTO trips (id, title, subtitle, created_at, updated_at, style,
           print_width, print_height, dpi, show_title, api_key_ref)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            new_trip_id,
            f"{trip['title']} (copy)",
            trip["subtitle"],
            now,
            now,
            trip["style"],
            trip["print_width"],
            trip["print_height"],
            trip["dpi"],
            trip["show_title"],
            trip["api_key_ref"],
        ),
    )
    for stop in trip.get("stops", []):
        new_stop_id = _uuid()
        await db.execute(
            """INSERT INTO stops (id, trip_id, sort_order, city, label, lat, lon,
               dates, nights, highlight, photo_path, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                new_stop_id,
                new_trip_id,
                stop["sort_order"],
                stop["city"],
                stop["label"],
                stop["lat"],
                stop["lon"],
                stop["dates"],
                stop["nights"],
                stop["highlight"],
                None,  # don't copy photos
                now,
            ),
        )
    await db.commit()
    return await get_trip_with_stops(db, new_trip_id)


async def export_trip_yaml(db: aiosqlite.Connection, trip_id: str) -> str | None:
    trip = await get_trip_with_stops(db, trip_id)
    if trip is None:
        return None
    data = {
        "title": trip["title"],
        "subtitle": trip["subtitle"],
        "style": trip["style"],
        "print_width": trip["print_width"],
        "print_height": trip["print_height"],
        "dpi": trip["dpi"],
        "stops": [
            {
                "city": s["city"],
                "label": s["label"],
                "lat": s["lat"],
                "lon": s["lon"],
                "dates": s["dates"],
                "nights": s["nights"],
                "highlight": bool(s["highlight"]),
            }
            for s in trip.get("stops", [])
        ],
    }
    return yaml.dump(data, default_flow_style=False, allow_unicode=True)


async def import_trip_yaml(db: aiosqlite.Connection, yaml_content: str) -> dict:
    data = yaml.safe_load(yaml_content)
    trip_id = _uuid()
    now = _now()
    await db.execute(
        """INSERT INTO trips (id, title, subtitle, created_at, updated_at, style,
           print_width, print_height, dpi)
           VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
        (
            trip_id,
            data.get("title", "Imported Trip"),
            data.get("subtitle", ""),
            now,
            now,
            data.get("style", "watercolor"),
            data.get("print_width", 24.0),
            data.get("print_height", 18.0),
            data.get("dpi", 300),
        ),
    )
    for i, stop in enumerate(data.get("stops", [])):
        stop_id = _uuid()
        await db.execute(
            """INSERT INTO stops (id, trip_id, sort_order, city, label, lat, lon,
               dates, nights, highlight, created_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (
                stop_id,
                trip_id,
                i,
                stop["city"],
                stop.get("label"),
                stop["lat"],
                stop["lon"],
                stop.get("dates", ""),
                stop.get("nights", 0),
                int(stop.get("highlight", False)),
                now,
            ),
        )
    await db.commit()
    return await get_trip_with_stops(db, trip_id)
