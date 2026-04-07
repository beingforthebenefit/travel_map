"""Tests for the OSRM routing service."""
import pytest
from unittest.mock import AsyncMock, patch, MagicMock

pytestmark = pytest.mark.asyncio


STOPS = [
    {"lat": 40.4168, "lon": -3.7038},   # Madrid
    {"lat": 38.7223, "lon": -9.1393},   # Lisbon
]

OSRM_OK_RESPONSE = {
    "code": "Ok",
    "routes": [{
        "geometry": {
            "coordinates": [
                [-3.7038, 40.4168],
                [-5.0,    39.5],
                [-9.1393, 38.7223],
            ]
        }
    }]
}


async def test_fetch_road_waypoints_success():
    from app.services.routing_service import fetch_road_waypoints

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=OSRM_OK_RESPONSE)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.routing_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_road_waypoints(STOPS)

    assert result is not None
    assert len(result) == 3
    # OSRM returns [lon, lat] — we flip to (lat, lon)
    assert result[0] == pytest.approx((40.4168, -3.7038))
    assert result[-1] == pytest.approx((38.7223, -9.1393))


async def test_fetch_road_waypoints_http_error_returns_none():
    from app.services.routing_service import fetch_road_waypoints
    import httpx

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(side_effect=httpx.HTTPError("timeout"))

    with patch("app.services.routing_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_road_waypoints(STOPS)

    assert result is None


async def test_fetch_road_waypoints_bad_osrm_code_returns_none():
    from app.services.routing_service import fetch_road_waypoints

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value={"code": "NoRoute", "routes": []})

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.routing_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_road_waypoints(STOPS)

    assert result is None


async def test_fetch_road_waypoints_single_stop_returns_none():
    from app.services.routing_service import fetch_road_waypoints
    result = await fetch_road_waypoints([STOPS[0]])
    assert result is None


async def test_fetch_road_waypoints_loop_appends_first_stop():
    """With loop=True, the first stop should be appended to close the route."""
    from app.services.routing_service import fetch_road_waypoints

    captured_url = []

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=OSRM_OK_RESPONSE)

    async def fake_get(url, **kwargs):
        captured_url.append(url)
        return mock_resp

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = fake_get

    with patch("app.services.routing_service.httpx.AsyncClient", return_value=mock_client):
        await fetch_road_waypoints(STOPS, loop=True)

    url = captured_url[0]
    # URL should contain 3 coordinate pairs (Madrid, Lisbon, Madrid again)
    assert url.count(";") == 2


async def test_fetch_road_waypoints_geojson_format():
    """geojson helper should return [[lat, lon], ...] lists."""
    from app.services.routing_service import fetch_road_waypoints_geojson

    mock_resp = MagicMock()
    mock_resp.raise_for_status = MagicMock()
    mock_resp.json = MagicMock(return_value=OSRM_OK_RESPONSE)

    mock_client = AsyncMock()
    mock_client.__aenter__ = AsyncMock(return_value=mock_client)
    mock_client.__aexit__ = AsyncMock(return_value=False)
    mock_client.get = AsyncMock(return_value=mock_resp)

    with patch("app.services.routing_service.httpx.AsyncClient", return_value=mock_client):
        result = await fetch_road_waypoints_geojson(STOPS)

    assert result is not None
    assert isinstance(result[0], list)
    assert len(result[0]) == 2
