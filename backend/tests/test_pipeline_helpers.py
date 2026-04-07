"""Tests for pipeline helper functions: geo distance and nearby-stop merging."""
import pytest
from app.renderer.pipeline import _geo_distance_km, _merge_nearby_stops


# --- _geo_distance_km ---

def test_geo_distance_same_point():
    assert _geo_distance_km(40.0, -3.7, 40.0, -3.7) == pytest.approx(0.0, abs=0.01)


def test_geo_distance_lisbon_sintra():
    """Lisbon and Sintra are about 23 km apart."""
    d = _geo_distance_km(38.7223, -9.1393, 38.7998, -9.3871)
    assert 20 < d < 30


def test_geo_distance_madrid_segovia():
    """Madrid and Segovia are about 67 km apart — should not merge."""
    d = _geo_distance_km(40.4168, -3.7038, 40.9429, -4.1088)
    assert 60 < d < 80


# --- _merge_nearby_stops ---

LISBON = {"city": "Lisbon",  "lat": 38.7223, "lon": -9.1393, "dates": "Mar 30–Apr 2",
          "highlight": True,  "photo_path": None, "id": "a", "sort_order": 0}
SINTRA = {"city": "Sintra",  "lat": 38.7998, "lon": -9.3871, "dates": "Apr 2–3",
          "highlight": False, "photo_path": None, "id": "b", "sort_order": 1}
PORTO  = {"city": "Porto",   "lat": 41.1579, "lon": -8.6291, "dates": "Apr 3–5",
          "highlight": True,  "photo_path": None, "id": "c", "sort_order": 2}
MADRID = {"city": "Madrid",  "lat": 40.4168, "lon": -3.7038, "dates": "Mar 22–24",
          "highlight": True,  "photo_path": None, "id": "d", "sort_order": 3}


def test_merge_close_stops():
    """Lisbon & Sintra (~23 km) should be merged into one point."""
    merged = _merge_nearby_stops([LISBON, SINTRA, PORTO])
    assert len(merged) == 2


def test_merge_combined_city_name():
    merged = _merge_nearby_stops([LISBON, SINTRA, PORTO])
    label = merged[0].get("label") or merged[0]["city"]
    assert "Lisbon" in label
    assert "Sintra" in label


def test_merge_combined_dates():
    merged = _merge_nearby_stops([LISBON, SINTRA, PORTO])
    assert LISBON["dates"] in merged[0]["dates"]
    assert SINTRA["dates"] in merged[0]["dates"]


def test_merge_inherits_highlight():
    """Merged stop should be highlighted if any stop in the group is."""
    merged = _merge_nearby_stops([LISBON, SINTRA])
    assert merged[0]["highlight"] is True


def test_merge_inherits_photo():
    """Merged stop should use the first photo found in the group."""
    lisbon_with_photo = {**LISBON, "photo_path": "lisbon.jpg"}
    merged = _merge_nearby_stops([lisbon_with_photo, SINTRA])
    assert merged[0]["photo_path"] == "lisbon.jpg"


def test_merge_distant_stops_unchanged():
    """Stops farther than threshold should not be merged."""
    merged = _merge_nearby_stops([MADRID, PORTO])
    assert len(merged) == 2


def test_merge_single_stop_unchanged():
    merged = _merge_nearby_stops([MADRID])
    assert len(merged) == 1
    assert merged[0]["city"] == "Madrid"


def test_merge_empty_list():
    assert _merge_nearby_stops([]) == []


def test_merge_average_position():
    """Merged lat/lon should be the average of the group."""
    merged = _merge_nearby_stops([LISBON, SINTRA])
    expected_lat = (LISBON["lat"] + SINTRA["lat"]) / 2
    expected_lon = (LISBON["lon"] + SINTRA["lon"]) / 2
    assert merged[0]["lat"] == pytest.approx(expected_lat)
    assert merged[0]["lon"] == pytest.approx(expected_lon)


def test_merge_preserves_order_of_remaining_stops():
    """After merging, non-merged stops should retain their original relative order."""
    stops = [MADRID, LISBON, SINTRA, PORTO]
    merged = _merge_nearby_stops(stops)
    # Madrid first, then Lisbon&Sintra, then Porto
    assert merged[0]["city"] == "Madrid"
    assert merged[-1]["city"] == "Porto"
