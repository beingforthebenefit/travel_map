import pytest
from pathlib import Path

pytestmark = pytest.mark.asyncio


async def _create_trip(client) -> str:
    resp = await client.post("/api/v1/trips", json={"title": "Test Trip"})
    return resp.json()["id"]


async def _add_stop(client, trip_id: str, city: str, lat: float, lon: float) -> dict:
    resp = await client.post(
        f"/api/v1/trips/{trip_id}/stops",
        json={"city": city, "dates": "Mar 1", "lat": lat, "lon": lon},
    )
    return resp.json()


async def test_add_stop(client):
    trip_id = await _create_trip(client)
    resp = await client.post(
        f"/api/v1/trips/{trip_id}/stops",
        json={"city": "Madrid", "dates": "Mar 22", "lat": 40.4, "lon": -3.7},
    )
    assert resp.status_code == 201
    stop = resp.json()
    assert stop["city"] == "Madrid"
    assert stop["sort_order"] == 0


async def test_add_multiple_stops_ordering(client):
    trip_id = await _create_trip(client)
    s1 = await _add_stop(client, trip_id, "Madrid", 40.4, -3.7)
    s2 = await _add_stop(client, trip_id, "Lisbon", 38.7, -9.1)
    assert s1["sort_order"] == 0
    assert s2["sort_order"] == 1


async def test_update_stop(client):
    trip_id = await _create_trip(client)
    stop = await _add_stop(client, trip_id, "Madrid", 40.4, -3.7)
    resp = await client.put(
        f"/api/v1/trips/{trip_id}/stops/{stop['id']}",
        json={"city": "Barcelona"},
    )
    assert resp.status_code == 200
    assert resp.json()["city"] == "Barcelona"


async def test_delete_stop(client):
    trip_id = await _create_trip(client)
    stop = await _add_stop(client, trip_id, "Madrid", 40.4, -3.7)
    resp = await client.delete(f"/api/v1/trips/{trip_id}/stops/{stop['id']}")
    assert resp.status_code == 204

    # Verify trip has 0 stops
    resp = await client.get(f"/api/v1/trips/{trip_id}")
    assert len(resp.json()["stops"]) == 0


async def test_reorder_stops(client):
    trip_id = await _create_trip(client)
    s1 = await _add_stop(client, trip_id, "Madrid", 40.4, -3.7)
    s2 = await _add_stop(client, trip_id, "Lisbon", 38.7, -9.1)
    s3 = await _add_stop(client, trip_id, "Porto", 41.1, -8.6)

    # Reverse order
    resp = await client.put(
        f"/api/v1/trips/{trip_id}/stops/reorder",
        json={"stop_ids": [s3["id"], s2["id"], s1["id"]]},
    )
    assert resp.status_code == 200
    stops = resp.json()
    assert stops[0]["city"] == "Porto"
    assert stops[1]["city"] == "Lisbon"
    assert stops[2]["city"] == "Madrid"


async def test_photo_upload_and_delete(client, tmp_data_dir):
    trip_id = await _create_trip(client)
    stop = await _add_stop(client, trip_id, "Madrid", 40.4, -3.7)

    # Create a minimal JPEG
    from PIL import Image
    import io
    img = Image.new("RGB", (100, 100), "red")
    buf = io.BytesIO()
    img.save(buf, "JPEG")
    buf.seek(0)

    resp = await client.post(
        f"/api/v1/trips/{trip_id}/stops/{stop['id']}/photo",
        files={"file": ("photo.jpg", buf, "image/jpeg")},
    )
    assert resp.status_code == 200
    assert resp.json()["photo_path"] is not None

    # Verify thumbnail was created
    thumb = tmp_data_dir / "trips" / trip_id / "photos" / f"{stop['id']}_thumb.jpg"
    assert thumb.exists()

    # Delete photo
    resp = await client.delete(f"/api/v1/trips/{trip_id}/stops/{stop['id']}/photo")
    assert resp.status_code == 204
    assert not thumb.exists()
