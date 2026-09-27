from fastapi.testclient import TestClient

from backend.app.main import app


client = TestClient(app)


def test_health_and_end_to_end_contract_on_committed_sample():
    health = client.get("/api/health")
    assert health.status_code == 200
    stations = client.get("/api/stations")
    assert stations.status_code == 200
    body = stations.json()
    assert body["stations"]
    location_id = body["stations"][0]["id"]

    hotspots = client.get("/api/hotspots?mode=before")
    attribution = client.get(f"/api/attribution?location_id={location_id}")
    backtest = client.get(f"/api/backtest?location_id={location_id}")
    forecast = client.get(f"/api/forecast?location_id={location_id}&hours=24")
    scenario = client.post(
        "/api/scenarios",
        json={"location_id": location_id, "cuts": {"traffic": 20, "industry": 30, "dust": 30}},
    )

    for response in [hotspots, attribution, backtest, forecast, scenario]:
        assert response.status_code == 200, response.text
        payload = response.json()
        assert payload["source_type"] in {"observed", "modeled", "synthetic"}
        assert "assumptions" in payload

    assert len(hotspots.json()["cells"]) == 144
    assert len(scenario.json()["results"]) == 4
