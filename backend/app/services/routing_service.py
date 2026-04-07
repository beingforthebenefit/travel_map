"""Road routing via the public OSRM demo server."""
import httpx


OSRM_BASE = "https://router.project-osrm.org/route/v1/driving"


async def fetch_road_waypoints(
    stops: list[dict],
    loop: bool = False,
) -> list[tuple[float, float]] | None:
    """Return (lat, lon) waypoints for a road route connecting the given stops.

    Uses the OSRM public demo API. Returns None on failure so callers can fall
    back to straight-line rendering.
    """
    if len(stops) < 2:
        return None

    pts = list(stops)
    if loop:
        pts = pts + [pts[0]]

    coord_str = ";".join(f"{s['lon']},{s['lat']}" for s in pts)
    url = f"{OSRM_BASE}/{coord_str}?overview=full&geometries=geojson"

    try:
        async with httpx.AsyncClient(timeout=20) as client:
            resp = await client.get(url, headers={"User-Agent": "travel_map/1.0"})
            resp.raise_for_status()
            data = resp.json()
    except Exception:
        return None

    if data.get("code") != "Ok" or not data.get("routes"):
        return None

    # OSRM returns [lon, lat] pairs
    coords = data["routes"][0]["geometry"]["coordinates"]
    return [(lat, lon) for lon, lat in coords]


async def fetch_road_waypoints_geojson(
    stops: list[dict],
    loop: bool = False,
) -> list[list[float]] | None:
    """Same as fetch_road_waypoints but returns [[lat, lon], ...] for JSON serialisation."""
    wps = await fetch_road_waypoints(stops, loop=loop)
    if wps is None:
        return None
    return [[lat, lon] for lat, lon in wps]
