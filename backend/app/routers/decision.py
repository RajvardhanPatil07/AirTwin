"""Versioned decision-workspace routes; original /api/* remains backward compatible."""
from __future__ import annotations

import logging
from fastapi import APIRouter, HTTPException, Query
from typing import Literal
from pydantic import BaseModel, Field
from app.schemas import Cuts, Region
from app.services import decision_store
from app.services.state_data import get_region_runtime

LOG = logging.getLogger("airtwin.decisions")
router = APIRouter(prefix="/v2", tags=["Decision workspace"])


class DecisionRequest(BaseModel):
    region: Region = "pcmc"
    location_id: str = Field(min_length=1, max_length=120)
    cuts: Cuts
    replay_at: str | None = None


@router.post("/decision-runs")
def run_decision(body: DecisionRequest):
    runtime = get_region_runtime(body.region, body.replay_at)
    # The existing scenario service enforces bounded reductions and sensitivity.
    result = runtime.scenario(body.location_id, body.cuts.model_dump(), body.replay_at)
    location, *_ = runtime.location(body.location_id, body.replay_at)
    saved_id = None
    storage_warning = None
    if decision_store.enabled():
        try:
            saved_id = decision_store.save_scenario(
                region=body.region, location_id=body.location_id,
                input_source_type=location["source_type"],
                cuts=body.cuts.model_dump(), scenario=result, replay_at=body.replay_at,
            )
        except Exception:
            LOG.warning("Decision run completed but could not be saved", exc_info=True)
            storage_warning = "Decision computed, but PostgreSQL persistence is unavailable."
    else:
        storage_warning = "DATABASE_URL is unset; this result has not been saved."
    return {
        "scenario": result, "run_id": saved_id, "persisted": bool(saved_id),
        "storage_warning": storage_warning, "source_type": "modeled",
        "assumptions": [
            "Policy effects are proxy hypotheses, not verified causal reductions.",
            "All scenario output is MODELED even when input PM2.5 is OBSERVED.",
            *result["assumptions"],
        ],
    }


@router.get("/decision-runs")
def list_decision_runs(region: Region = "pcmc", limit: int = Query(15, ge=1, le=50)):
    try:
        records = decision_store.recent_runs(region, limit)
    except Exception:
        LOG.warning("Decision run history unavailable", exc_info=True)
        raise HTTPException(status_code=503, detail="Decision history database unavailable")
    return {
        "records": records,
        "source_type": "modeled",
        "assumptions": ["Historical scenarios are modeled counterfactuals; they are not observed outcomes."],
        "database": decision_store.safe_overview(region),
    }


@router.get("/data-health")
def data_health(region: Region = "pcmc"):
    storage = decision_store.safe_overview(region)
    return {
        "region": region, "database": storage,
        "source_type": "modeled",
        "assumptions": [
            "CAMS is a modeled atmospheric reference, not an air-quality station.",
            "Provider observations retain their original timestamps and source labels.",
            "IDW maps are modeled interpolations, not measured values.",
            "Only explicitly run scenarios are stored in decision_runs.",
        ],
    }


@router.get("/hotspot-summary")
def hotspot_summary(region: Region = "pcmc"):
    runtime = get_region_runtime(region, None)
    stations, cells, _, _, timestamp = runtime.snapshot()
    top = sorted(cells, key=lambda cell: cell["pm25"], reverse=True)[:5]
    return {
        "region": region, "as_of": timestamp.isoformat(),
        "source_type": "modeled",
        "assumptions": [
            "Ranked hotspot grid concentrations are IDW estimates rather than direct observations.",
            "Hotspot ranking applies only to the sampled model grid, not every city street.",
        ],
        "grid_count": len(cells),
        "station_count": len(stations),
        "hotspots": [
            {"cell_id": cell["id"], "pm25": cell["pm25"],
             "latitude": cell["latitude"], "longitude": cell["longitude"]}
            for cell in top
        ],
    }


@router.get("/samples")
def samples(region: Region = "pcmc",
            source_type: Literal["observed", "modeled", "synthetic"] | None = None,
            limit: int = Query(50, ge=1, le=100)):
    try:
        readings = decision_store.recent_samples(region, source_type, limit)
    except Exception:
        LOG.warning("Sample history unavailable", exc_info=True)
        raise HTTPException(status_code=503, detail="Sample database unavailable")
    return {
        "region": region,
        "samples": readings,
        "source_type": "modeled",
        "assumptions": [
            "Each sample carries its own source_type; modeled CAMS fields are not observed station readings.",
            "No gridded interpolation or intervention output is stored as an observed sample.",
            "The collection is query metadata. Use each row's source_type when interpreting its value.",
        ],
    }
