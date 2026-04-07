import pytest
from pathlib import Path

pytestmark = pytest.mark.asyncio


async def test_create_trip(client):
    resp = await client.post("/api/v1/trips", json={"title": "Test Trip", "subtitle": "Sub"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["title"] == "Test Trip"
    assert data["subtitle"] == "Sub"
    assert data["id"]
    assert data["stops"] == []


async def test_list_trips(client):
    await client.post("/api/v1/trips", json={"title": "Trip 1"})
    await client.post("/api/v1/trips", json={"title": "Trip 2"})
    resp = await client.get("/api/v1/trips")
    assert resp.status_code == 200
    trips = resp.json()
    assert len(trips) == 2
    assert all("stop_count" in t for t in trips)


async def test_get_trip(client):
    create = await client.post("/api/v1/trips", json={"title": "My Trip"})
    trip_id = create.json()["id"]
    resp = await client.get(f"/api/v1/trips/{trip_id}")
    assert resp.status_code == 200
    assert resp.json()["title"] == "My Trip"


async def test_get_trip_not_found(client):
    resp = await client.get("/api/v1/trips/nonexistent")
    assert resp.status_code == 404


async def test_update_trip(client):
    create = await client.post("/api/v1/trips", json={"title": "Old"})
    trip_id = create.json()["id"]
    resp = await client.put(f"/api/v1/trips/{trip_id}", json={"title": "New"})
    assert resp.status_code == 200
    assert resp.json()["title"] == "New"


async def test_delete_trip(client):
    create = await client.post("/api/v1/trips", json={"title": "Doomed"})
    trip_id = create.json()["id"]
    resp = await client.delete(f"/api/v1/trips/{trip_id}")
    assert resp.status_code == 204
    resp = await client.get(f"/api/v1/trips/{trip_id}")
    assert resp.status_code == 404


async def test_duplicate_trip(client):
    create = await client.post("/api/v1/trips", json={"title": "Original"})
    trip_id = create.json()["id"]
    # Add a stop
    await client.post(
        f"/api/v1/trips/{trip_id}/stops",
        json={"city": "Madrid", "dates": "Mar 22", "lat": 40.4, "lon": -3.7},
    )
    resp = await client.post(f"/api/v1/trips/{trip_id}/duplicate")
    assert resp.status_code == 201
    dup = resp.json()
    assert dup["title"] == "Original (copy)"
    assert len(dup["stops"]) == 1
    assert dup["id"] != trip_id


async def test_trip_has_route_type_field(client):
    resp = await client.post("/api/v1/trips", json={"title": "Route test"})
    assert resp.status_code == 201
    data = resp.json()
    assert data["route_type"] == "straight"


async def test_update_route_type(client):
    create = await client.post("/api/v1/trips", json={"title": "Route test"})
    trip_id = create.json()["id"]
    resp = await client.put(f"/api/v1/trips/{trip_id}", json={"route_type": "roads"})
    assert resp.status_code == 200
    assert resp.json()["route_type"] == "roads"


async def test_update_route_type_invalid_is_ignored(client):
    create = await client.post("/api/v1/trips", json={"title": "Route test"})
    trip_id = create.json()["id"]
    # Update with invalid value — should be silently ignored, value stays "straight"
    resp = await client.put(f"/api/v1/trips/{trip_id}", json={"route_type": "teleport"})
    assert resp.status_code == 200
    assert resp.json()["route_type"] == "straight"


async def test_road_route_endpoint_no_stops_returns_error(client):
    create = await client.post("/api/v1/trips", json={"title": "Empty"})
    trip_id = create.json()["id"]
    # With no stops, routing service returns None → 502
    resp = await client.get(f"/api/v1/trips/{trip_id}/road-route")
    assert resp.status_code == 502


async def test_import_export_roundtrip(client):
    fixture = Path(__file__).parent / "fixtures" / "sample_trip.yaml"
    with open(fixture, "rb") as f:
        resp = await client.post(
            "/api/v1/trips/import",
            files={"file": ("trip.yaml", f, "application/x-yaml")},
        )
    assert resp.status_code == 201
    trip = resp.json()
    assert trip["title"] == "Spain & Portugal 2026"
    assert len(trip["stops"]) == 11

    # Export
    resp = await client.get(f"/api/v1/trips/{trip['id']}/export")
    assert resp.status_code == 200
    assert "Madrid" in resp.text
