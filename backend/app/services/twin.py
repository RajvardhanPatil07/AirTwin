"""Spatial hotspot, attribution and intervention engine for AirTwin.

This module is intentionally transparent: spatial interpolation and source
attribution are proxy models, not chemical source apportionment. Every public
response carries those assumptions so the UI can keep observed and modeled
results separate.
"""
from __future__ import annotations

import math
from uuid import NAMESPACE_URL, uuid5

import numpy as np
import pandas as pd

from ..config import BBOX, TIMEZONE, WEATHER_COLUMNS

GRID_SIZE = 12
PASS_THROUGH = 0.70
ACTION_LIMITS = {"traffic": 50.0, "industry": 60.0, "dust": 70.0}
ACTION_NAMES = {
    "traffic": "Traffic restriction",
    "industry": "Industrial controls",
    "dust": "Dust suppression",
}
TRAFFIC_ANCHOR = (18.630, 73.800)
INDUSTRY_ANCHORS = ((18.620, 73.850), (18.760, 73.860))
DUST_ANCHOR = (18.590, 73.740)

SPATIAL_ASSUMPTIONS = [
    "Hotspot cells are inverse-distance interpolation of the latest available station values; cells are MODELED, not observations.",
    "Traffic, industry and dust shares are transparent spatial/weather proxies, not chemical source-apportionment measurements.",
    "Regional background is the 15th percentile of latest station concentrations, capped at each cell baseline.",
    "Scenario cuts act only on local excess above background with a central concentration pass-through of 0.70.",
    "Population is a synthetic density surface used only for relative exposure-benefit ranking.",
]


def _source_type(values) -> str:
    kinds = {str(value) for value in values if pd.notna(value)}
    if kinds == {"observed"}:
        return "observed"
    if kinds == {"synthetic"}:
        return "synthetic"
    return "modeled"


def _latest_rows(frame: pd.DataFrame) -> pd.DataFrame:
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce").dt.tz_convert(TIMEZONE)
    data["pm25"] = pd.to_numeric(data["pm25"], errors="coerce")
    data["latitude"] = pd.to_numeric(data["latitude"], errors="coerce")
    data["longitude"] = pd.to_numeric(data["longitude"], errors="coerce")
    data = data.dropna(subset=["timestamp", "station_id", "latitude", "longitude", "pm25"])
    if data.empty:
        raise ValueError("Dataset has no usable PM2.5 station rows")
    return (
        data.sort_values("timestamp")
        .groupby(data["station_id"].astype(str), as_index=False, group_keys=False)
        .tail(1)
        .reset_index(drop=True)
    )


def stations_response(frame: pd.DataFrame) -> dict:
    latest = _latest_rows(frame)
    stations = []
    for row in latest.itertuples(index=False):
        source = str(row.source_type) if str(row.source_type) in {"observed", "modeled", "synthetic"} else "modeled"
        name = str(row.station_name)
        stations.append(
            {
                "id": str(row.station_id),
                "name": name,
                "short_name": name.replace(" monitoring station", "")[:28],
                "latitude": float(row.latitude),
                "longitude": float(row.longitude),
                "pm25": float(row.pm25),
                "timestamp": row.timestamp.isoformat(),
                "source_type": source,
                "assumptions": [] if source == "observed" else [
                    "This location value is not an observed monitoring reading; inspect its source_type and provider before presenting it."
                ],
            }
        )
    return {
        "stations": stations,
        "source_type": _source_type(latest["source_type"]),
        "assumptions": [
            "Response-level provenance summarizes the station set; each station retains its own source_type."
        ],
    }


def _distance2(lat: float, lon: float, target_lat: float, target_lon: float) -> float:
    return (lat - target_lat) ** 2 + ((lon - target_lon) * math.cos(math.radians(lat))) ** 2


def _idw(lat: float, lon: float, stations: pd.DataFrame) -> float:
    weighted = 0.0
    total = 0.0
    for row in stations.itertuples(index=False):
        distance2 = _distance2(lat, lon, float(row.latitude), float(row.longitude))
        if distance2 < 1e-12:
            return float(row.pm25)
        weight = 1.0 / distance2
        weighted += float(row.pm25) * weight
        total += weight
    return weighted / total if total else 0.0


def _weather_snapshot(frame: pd.DataFrame) -> dict[str, float]:
    data = frame.copy()
    data["timestamp"] = pd.to_datetime(data["timestamp"], utc=True, errors="coerce")
    data = data.sort_values("timestamp")
    result = {}
    for column in WEATHER_COLUMNS:
        values = pd.to_numeric(data.get(column), errors="coerce") if column in data else pd.Series(dtype=float)
        values = values.dropna()
        result[column] = float(values.iloc[-1]) if not values.empty else float("nan")
    return result


def _proximity(lat: float, lon: float, anchor: tuple[float, float], scale: float = 0.003) -> float:
    return math.exp(-((lat - anchor[0]) ** 2 + (lon - anchor[1]) ** 2) / scale)


def local_weights(lat: float, lon: float, weather: dict[str, float] | None = None) -> dict[str, float]:
    weather = weather or {}
    wind = weather.get("wind_speed_10m", float("nan"))
    humidity = weather.get("relative_humidity_2m", float("nan"))
    precipitation = weather.get("precipitation", float("nan"))

    wind = 3.0 if not np.isfinite(wind) else max(0.0, float(wind))
    humidity = 60.0 if not np.isfinite(humidity) else min(100.0, max(0.0, float(humidity)))
    precipitation = 0.0 if not np.isfinite(precipitation) else max(0.0, float(precipitation))

    calm_factor = 1.0 + max(0.0, 3.0 - wind) / 6.0
    dryness_factor = 1.0 + max(0.0, 55.0 - humidity) / 100.0
    rain_suppression = 1.0 / (1.0 + 0.35 * precipitation)

    traffic = (0.65 + 0.75 * _proximity(lat, lon, TRAFFIC_ANCHOR)) * calm_factor
    industry = (
        0.35
        + 2.0 * sum(_proximity(lat, lon, anchor) for anchor in INDUSTRY_ANCHORS)
    ) * calm_factor
    dust = (0.45 + 0.85 * _proximity(lat, lon, DUST_ANCHOR)) * dryness_factor * rain_suppression
    total = traffic + industry + dust
    return {
        "traffic": traffic / total,
        "industry": industry / total,
        "dust": dust / total,
    }


def _population(lat: float, lon: float) -> int:
    return int(round(700 + 9000 * math.exp(-((lat - 18.60) ** 2 + (lon - 73.83) ** 2) / 0.009)))


def _background(stations: pd.DataFrame) -> float:
    return float(np.quantile(stations["pm25"].to_numpy(dtype=float), 0.15))


def grid_cells(frame: pd.DataFrame) -> list[dict]:
    stations = _latest_rows(frame)
    weather = _weather_snapshot(frame)
    regional = _background(stations)
    west, south, east, north = BBOX
    dy = (north - south) / GRID_SIZE
    dx = (east - west) / GRID_SIZE
    cells = []
    for row in range(GRID_SIZE):
        for col in range(GRID_SIZE):
            cell_south = south + row * dy
            cell_west = west + col * dx
            lat = cell_south + dy / 2
            lon = cell_west + dx / 2
            value = _idw(lat, lon, stations)
            cells.append(
                {
                    "id": f"cell-{row}-{col}",
                    "latitude": lat,
                    "longitude": lon,
                    "bounds": [[cell_south, cell_west], [cell_south + dy, cell_west + dx]],
                    "pm25": value,
                    "background": min(regional, value),
                    "population": _population(lat, lon),
                    "population_source_type": "synthetic",
                    "local_weights": local_weights(lat, lon, weather),
                    "source_type": "modeled",
                    "assumptions": SPATIAL_ASSUMPTIONS,
                }
            )
    return cells


def hotspots_response(frame: pd.DataFrame) -> dict:
    return {
        "cells": grid_cells(frame),
        "source_type": "modeled",
        "assumptions": SPATIAL_ASSUMPTIONS,
    }


def _station(frame: pd.DataFrame, location_id: str) -> pd.Series:
    latest = _latest_rows(frame)
    selected = latest[latest["station_id"].astype(str) == str(location_id)]
    if selected.empty:
        raise KeyError(f"Unknown station_id: {location_id}")
    return selected.iloc[0]


def attribution_response(frame: pd.DataFrame, location_id: str) -> dict:
    row = _station(frame, location_id)
    stations = _latest_rows(frame)
    regional = min(_background(stations), float(row.pm25))
    weights = local_weights(float(row.latitude), float(row.longitude), _weather_snapshot(frame))
    concentration = max(float(row.pm25), 0.0)
    excess = max(concentration - regional, 0.0)
    if concentration <= 0:
        shares = {"traffic": 0.0, "industry": 0.0, "dust": 0.0, "background": 1.0}
    else:
        shares = {
            "traffic": weights["traffic"] * excess / concentration,
            "industry": weights["industry"] * excess / concentration,
            "dust": weights["dust"] * excess / concentration,
            "background": regional / concentration,
        }
    return {
        "location_id": str(location_id),
        "background": regional,
        "shares": [
            {"name": "Traffic", "value": shares["traffic"], "color": "#0b4f6c"},
            {"name": "Industry", "value": shares["industry"], "color": "#b45309"},
            {"name": "Construction / road dust", "value": shares["dust"], "color": "#6b7280"},
            {"name": "Regional background", "value": shares["background"], "color": "#9bbdb0"},
        ],
        "source_type": "modeled",
        "assumptions": SPATIAL_ASSUMPTIONS,
    }


def _clamp_cuts(cuts: dict[str, float]) -> dict[str, float]:
    return {
        key: min(ACTION_LIMITS[key], max(0.0, float(cuts.get(key, 0.0))))
        for key in ACTION_LIMITS
    }


def _delta(value: float, background: float, weights: dict[str, float], cuts: dict[str, float], pass_through: float = PASS_THROUGH) -> float:
    weighted_cut = sum(weights[key] * cuts[key] / 100.0 for key in ACTION_LIMITS)
    return max(value - background, 0.0) * weighted_cut * pass_through


def scenario_response(frame: pd.DataFrame, location_id: str, requested_cuts: dict[str, float]) -> dict:
    row = _station(frame, location_id)
    base_cells = grid_cells(frame)
    stations = _latest_rows(frame)
    regional = min(_background(stations), float(row.pm25))
    weather = _weather_snapshot(frame)
    weights = local_weights(float(row.latitude), float(row.longitude), weather)
    cuts = _clamp_cuts(requested_cuts)
    packages = [
        ("combined", "Combined clean-air package", cuts),
        *[
            (
                action,
                ACTION_NAMES[action],
                {key: cuts[key] if key == action else 0.0 for key in ACTION_LIMITS},
            )
            for action in ACTION_LIMITS
        ],
    ]

    results = []
    for action_id, name, action_cuts in packages:
        reduction = _delta(float(row.pm25), regional, weights, action_cuts)
        after_cells = []
        exposure_benefit = 0.0
        for cell in base_cells:
            cell_reduction = _delta(
                float(cell["pm25"]),
                float(cell["background"]),
                cell["local_weights"],
                action_cuts,
            )
            after = max(float(cell["background"]), float(cell["pm25"]) - cell_reduction)
            exposure_benefit += cell_reduction * int(cell["population"])
            after_cells.append({**cell, "pm25": after})

        low = _delta(float(row.pm25), regional, weights, action_cuts, 0.60) * 0.80
        high = min(
            max(float(row.pm25) - regional, 0.0),
            _delta(float(row.pm25), regional, weights, action_cuts, 0.80) * 1.20,
        )
        results.append(
            {
                "id": action_id,
                "name": name,
                "cuts": action_cuts,
                "rank": 0,
                "before": float(row.pm25),
                "after": max(regional, float(row.pm25) - reduction),
                "reduction": reduction,
                "reduction_low": low,
                "reduction_high": high,
                "reduction_percent": (100 * reduction / float(row.pm25)) if float(row.pm25) > 0 else 0.0,
                "exposure_benefit": exposure_benefit,
                "population_source_type": "synthetic",
                "cells": after_cells,
                "source_type": "modeled",
                "assumptions": SPATIAL_ASSUMPTIONS,
            }
        )

    results.sort(key=lambda item: item["exposure_benefit"], reverse=True)
    for rank, result in enumerate(results, start=1):
        result["rank"] = rank

    scenario_key = f"{location_id}:{cuts['traffic']:.2f}:{cuts['industry']:.2f}:{cuts['dust']:.2f}"
    return {
        "scenario_id": str(uuid5(NAMESPACE_URL, f"airtwin:{scenario_key}")),
        "location_id": str(location_id),
        "results": results,
        "source_type": "modeled",
        "assumptions": SPATIAL_ASSUMPTIONS,
    }
