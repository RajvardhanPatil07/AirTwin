import json
from pathlib import Path
import pytest
from app.services.state_data import StateRuntime, SAMPLE, AIR_FIELDS, WEATHER_FIELDS
from app.services.regions import inside_state
from app.services.explainer import checked_claims

@pytest.fixture(scope='module')
def state():
    return StateRuntime(json.loads(SAMPLE.read_text()), sample=True)

def test_state_sample_and_boundary(state):
    assert SAMPLE.stat().st_size < 1_000_000
    response = state.stations()
    assert len(response['stations']) == 36
    assert all(p['source_type'] == 'modeled' for p in response['stations'])
    assert len(AIR_FIELDS + WEATHER_FIELDS) == 15
    assert inside_state(18.52, 73.86)
    assert not inside_state(28.61, 77.21)
    _, cells, _, _, _ = state.snapshot()
    assert cells and all(inside_state(c['latitude'], c['longitude']) for c in cells)

def test_state_forecast_and_no_invented_validation(state):
    location = state.stations()['stations'][0]['id']
    forecast = state.forecast(location, 72)
    assert len([p for p in forecast['series'] if p['predicted'] is not None]) == 72
    assert forecast['shap'] is None
    assert all(p['p10'] is None and p['p90'] is None for p in forecast['series'])
    assert state.backtest(location)['metrics'] is None
    results = state.scenario(location, {'traffic': 20, 'industry': 30, 'dust': 30})['results']
    combined = next(r for r in results if r['id'] == 'combined')
    assert combined['reduction'] == pytest.approx(sum(r['reduction'] for r in results if r['id'] != 'combined'))

def test_gemini_claim_checks():
    context = {'evidence': {'forecast': {'source_type': 'modeled', 'data': {'pm25': 34.2}}}}
    valid = {'claims': [{'text': 'Forecast concentration is 34.2.', 'source_type': 'modeled', 'evidence_ids': ['forecast']}]}
    assert checked_claims(valid, context) == valid['claims']
    with pytest.raises(ValueError):
        checked_claims({'claims': [{**valid['claims'][0], 'source_type': 'observed'}]}, context)
    with pytest.raises(ValueError):
        checked_claims({'claims': [{**valid['claims'][0], 'text': 'Concentration is 9999.'}]}, context)
