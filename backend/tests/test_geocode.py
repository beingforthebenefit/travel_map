import pytest
from unittest.mock import AsyncMock, MagicMock, patch

pytestmark = pytest.mark.asyncio


MOCK_RESPONSE = [
    {
        "display_name": "Madrid, Community of Madrid, Spain",
        "lat": "40.4167754",
        "lon": "-3.7037902",
    }
]


@patch("app.services.geocode_service.httpx.AsyncClient")
async def test_geocode_endpoint(mock_client_cls, client):
    mock_response = MagicMock()
    mock_response.json.return_value = MOCK_RESPONSE
    mock_response.raise_for_status = MagicMock()

    mock_instance = AsyncMock()
    mock_instance.get.return_value = mock_response
    mock_instance.__aenter__ = AsyncMock(return_value=mock_instance)
    mock_instance.__aexit__ = AsyncMock(return_value=False)
    mock_client_cls.return_value = mock_instance

    resp = await client.get("/api/v1/geocode", params={"q": "Madrid"})
    assert resp.status_code == 200
    data = resp.json()
    assert len(data) == 1
    assert data[0]["display_name"] == "Madrid, Community of Madrid, Spain"
    assert abs(data[0]["lat"] - 40.4168) < 0.01


@patch("app.services.geocode_service.httpx.AsyncClient")
async def test_geocode_empty_query(mock_client_cls, client):
    resp = await client.get("/api/v1/geocode", params={"q": ""})
    assert resp.status_code == 422  # validation error


async def test_settings_roundtrip(client):
    resp = await client.get("/api/v1/settings")
    assert resp.status_code == 200
    data = resp.json()
    assert data["default_style"] == "watercolor"
    assert data["stadia_api_key_set"] is False

    # Update
    resp = await client.put(
        "/api/v1/settings",
        json={"default_style": "dark", "default_dpi": 150},
    )
    assert resp.status_code == 200
    assert resp.json()["default_style"] == "dark"
    assert resp.json()["default_dpi"] == 150

    # Verify persistence
    resp = await client.get("/api/v1/settings")
    assert resp.json()["default_style"] == "dark"
