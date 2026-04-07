import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from pathlib import Path
from PIL import Image
import io

pytestmark = pytest.mark.asyncio


def _make_solid_tile(color=(100, 150, 200)):
    """Create a solid-color 256x256 tile as bytes."""
    img = Image.new("RGBA", (256, 256), (*color, 255))
    buf = io.BytesIO()
    img.save(buf, "PNG")
    return buf.getvalue()


async def test_render_pipeline_integration(client, tmp_data_dir):
    """Full integration test: create trip, add stops, render with mocked tiles."""
    # Create trip
    resp = await client.post("/api/v1/trips", json={"title": "Test Render", "subtitle": "Testing"})
    trip = resp.json()
    trip_id = trip["id"]

    # Add 3 stops
    stops_data = [
        {"city": "Madrid", "dates": "Mar 22", "lat": 40.4168, "lon": -3.7038},
        {"city": "Lisbon", "dates": "Mar 25", "lat": 38.7223, "lon": -9.1393},
        {"city": "Porto", "dates": "Mar 28", "lat": 41.1579, "lon": -8.6291},
    ]
    for s in stops_data:
        await client.post(f"/api/v1/trips/{trip_id}/stops", json=s)

    # Update trip to use small dimensions for fast test
    await client.put(
        f"/api/v1/trips/{trip_id}",
        json={"print_width": 4.0, "print_height": 3.0, "dpi": 50, "style": "positron"},
    )

    # Mock tile fetching to return solid tiles
    tile_bytes = _make_solid_tile()
    mock_response = MagicMock()
    mock_response.content = tile_bytes
    mock_response.raise_for_status = MagicMock()

    with patch("app.renderer.tiles.httpx.AsyncClient") as mock_client_cls:
        mock_instance = AsyncMock()
        mock_instance.get.return_value = mock_response
        mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
        mock_instance.__aexit__ = AsyncMock(return_value=False)
        mock_client_cls.return_value = mock_instance

        # Start render
        resp = await client.post(f"/api/v1/trips/{trip_id}/render", json={"style": "positron"})
        assert resp.status_code == 202
        job_id = resp.json()["job_id"]

        # Wait for render to complete
        import asyncio
        for _ in range(30):
            resp = await client.get(f"/api/v1/trips/{trip_id}/render/status")
            status = resp.json()
            if status["status"] in ("done", "error"):
                break
            await asyncio.sleep(0.2)

        assert status["status"] == "done", f"Render failed: {status.get('error')}"

    # Verify output file exists
    output = tmp_data_dir / "trips" / trip_id / "output" / "travel_map_positron.png"
    assert output.exists()

    # Verify dimensions (4 * 50 = 200, 3 * 50 = 150)
    img = Image.open(output)
    assert img.size == (200, 150)


async def test_render_no_stops(client):
    """Render with no stops should fail."""
    resp = await client.post("/api/v1/trips", json={"title": "Empty"})
    trip_id = resp.json()["id"]
    resp = await client.post(f"/api/v1/trips/{trip_id}/render", json={})
    assert resp.status_code == 400
