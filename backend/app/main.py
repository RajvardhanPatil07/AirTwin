"""FastAPI application exposing the ENR-01 AirTwin digital-twin contract."""
from __future__ import annotations

from functools import lru_cache

import pandas as pd
from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field

from .config import PROCESSED, SAMPLE
from .services.forecasting import backtest_response, forecast_response
from .services.twin import (
    attribution_response,
    hotspots_response,
    scenario_response,
    stations_response,
)

app = FastAPI(
    title="AirTwin PCMC API",
    version="0.2.0",
    description="Transparent PM2.5 forecast, attribution and intervention API for ENR-01.",
)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=False,
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type"],
)


class Cuts(BaseModel):
    traffic: float = Field(ge=0)
    industry: float = Field(ge=0)
    dust: float = Field(ge=0)


class ScenarioRequest(BaseModel):
    location_id: str = Field(min_length=1)
    cuts: Cuts


@lru_cache(maxsize=1)
def load_dataset() -> pd.DataFrame:
    parquet = PROCESSED / "dataset.parquet"
    if parquet.exists():
        frame = pd.read_parquet(parquet)
    elif SAMPLE.exists():
        frame = pd.read_csv(SAMPLE, dtype={"station_id": str})
    else:
        raise RuntimeError("No processed dataset or committed sample is available")
    required = {"timestamp", "station_id", "station_name", "latitude", "longitude", "pm25", "source_type"}
    missing = required - set(frame.columns)
    if missing:
        raise RuntimeError(f"Dataset missing required columns: {sorted(missing)}")
    return frame


def _call(service, *args):
    try:
        return service(load_dataset(), *args)
    except KeyError as error:
        raise HTTPException(status_code=404, detail=str(error)) from error
    except ValueError as error:
        raise HTTPException(status_code=422, detail=str(error)) from error
    except RuntimeError as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/health")
def health():
    try:
        frame = load_dataset()
        return {
            "status": "ok",
            "rows": int(len(frame)),
            "stations": int(frame["station_id"].astype(str).nunique()),
            "target_source_types": sorted(frame["source_type"].dropna().astype(str).unique().tolist()),
        }
    except Exception as error:
        raise HTTPException(status_code=503, detail=str(error)) from error


@app.get("/api/stations")
def stations():
    return _call(stations_response)


@app.get("/api/hotspots")
def hotspots(mode: str = Query("before", pattern="^before$")):
    return _call(hotspots_response)


@app.get("/api/forecast")
def forecast(location_id: str, hours: int = Query(24)):
    if hours not in {24, 48, 72}:
        raise HTTPException(status_code=422, detail="hours must be one of 24, 48 or 72")
    return _call(forecast_response, location_id, hours)


@app.get("/api/backtest")
def backtest(location_id: str):
    return _call(backtest_response, location_id)


@app.get("/api/attribution")
def attribution(location_id: str):
    return _call(attribution_response, location_id)


@app.post("/api/scenarios")
def scenarios(payload: ScenarioRequest):
    return _call(scenario_response, payload.location_id, payload.cuts.model_dump())
