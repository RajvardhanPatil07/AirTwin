import pandas as pd

from backend.app.services.twin import (
    attribution_response,
    hotspots_response,
    scenario_response,
    stations_response,
)


def frame():
    rows = []
    for station_id, name, lat, lon, value in [
        ("a", "Station A", 18.53, 73.85, 55.0),
        ("b", "Station B", 18.62, 73.85, 95.0),
        ("c", "Station C", 18.76, 73.86, 125.0),
    ]:
        rows.append(
            {
                "timestamp": "2026-01-10T10:00:00+05:30",
                "station_id": station_id,
                "station_name": name,
                "latitude": lat,
                "longitude": lon,
                "pm25": value,
                "source_type": "observed",
                "target_provider": "fixture",
                "temperature_2m": 28,
                "relative_humidity_2m": 45,
                "wind_speed_10m": 2,
                "wind_direction_10m": 90,
                "precipitation": 0,
                "weather_source_type": "modeled",
                "weather_provider": "fixture",
            }
        )
    return pd.DataFrame(rows)


def test_hotspot_grid_and_station_provenance():
    stations = stations_response(frame())
    hotspots = hotspots_response(frame())
    assert len(stations["stations"]) == 3
    assert all(station["source_type"] == "observed" for station in stations["stations"])
    assert hotspots["source_type"] == "modeled"
    assert len(hotspots["cells"]) == 144


def test_attribution_has_three_local_categories_plus_background():
    result = attribution_response(frame(), "b")
    assert len(result["shares"]) == 4
    assert abs(sum(item["value"] for item in result["shares"]) - 1.0) < 1e-9
    assert {item["name"] for item in result["shares"]} >= {"Traffic", "Industry", "Construction / road dust"}


def test_zero_cut_scenario_does_not_invent_a_reduction():
    result = scenario_response(frame(), "b", {"traffic": 0, "industry": 0, "dust": 0})
    combined = next(item for item in result["results"] if item["id"] == "combined")
    assert combined["reduction"] == 0
    assert combined["after"] == combined["before"]


def test_combined_package_is_at_least_each_individual_action():
    result = scenario_response(frame(), "b", {"traffic": 20, "industry": 30, "dust": 30})
    reductions = {item["id"]: item["reduction"] for item in result["results"]}
    assert reductions["combined"] >= reductions["traffic"]
    assert reductions["combined"] >= reductions["industry"]
    assert reductions["combined"] >= reductions["dust"]
