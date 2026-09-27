import sys
from pathlib import Path
import pytest
from fastapi.testclient import TestClient
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.main import app
from app.services.runtime import Runtime, get_runtime


@pytest.fixture(scope='module')
def client(tmp_path_factory):
    from app.services import model
    patch = pytest.MonkeyPatch()
    model_dir = tmp_path_factory.mktemp('models')
    patch.setattr(model, 'MODELS', model_dir)
    patch.setattr(model, 'ARTIFACT', model_dir / 'forecast.joblib')
    runtime = Runtime(force_sample=True)
    app.dependency_overrides.clear()
    # Routes share this cached runtime; tests never read keys or call providers.
    get_runtime.cache_clear()
    import app.services.runtime as module
    original = module.get_runtime
    import app.main as main
    from app.routers import forecast, backtest, map, attribution, scenarios, explain
    modules = [main, forecast, backtest, map, attribution, scenarios, explain]
    for target in modules:
        target.get_runtime = lambda: runtime
    with TestClient(app) as test_client:
        yield test_client
    for target in modules:
        target.get_runtime = original
    patch.undo()


def test_contract_and_provenance(client):
    health = client.get('/api/health').json()
    assert health['target_source_types'] == ['synthetic']
    stations = client.get('/api/stations').json()
    location = stations['stations'][0]['id']
    assert stations['stations'][0]['source_type'] == 'synthetic'
    for path in ['hotspots', f'forecast?location_id={location}&hours=72', f'backtest?location_id={location}', f'attribution?location_id={location}']:
        response = client.get('/api/' + path)
        assert response.status_code == 200, response.text
        assert response.json()['source_type'] == 'modeled'
        assert response.json()['assumptions']
    forecast = client.get(f'/api/forecast?location_id={location}').json()
    shap = forecast['shap']
    assert shap['base_value'] + sum(shap['groups'].values()) == pytest.approx(shap['prediction'], abs=1e-6)


def test_scenario_after_map_and_invalid_inputs(client):
    location = client.get('/api/stations').json()['stations'][0]['id']
    response = client.post('/api/scenarios', json={'location_id': location, 'cuts': {'traffic': 20, 'industry': 30, 'dust': 30}})
    assert response.status_code == 200
    scenario = response.json()
    combined = next(r for r in scenario['results'] if r['id'] == 'combined')
    grid = client.get('/api/hotspots', params={'mode': 'after', 'scenario_id': scenario['scenario_id']}).json()
    assert grid['cells'] == combined['cells']
    assert client.post('/api/scenarios', json={'location_id': location, 'cuts': {'traffic': -1, 'industry': 0, 'dust': 0}}).status_code == 422
    assert client.get('/api/hotspots?mode=after&scenario_id=missing').status_code == 404
    assert client.get('/api/forecast?location_id=missing').status_code == 404
    assert client.get(f'/api/forecast?location_id={location}&hours=100').status_code == 422


def test_replay_and_explainer_template(client, monkeypatch):
    monkeypatch.delenv('LLM_API_KEY', raising=False)
    replay = client.get('/api/replay').json()
    stations = client.get('/api/stations', params={'replay_at': replay['timestamp']}).json()
    assert stations['data_mode'] == 'historical_replay'
    replay_forecast = client.get('/api/forecast', params={'location_id': replay['location_id'], 'replay_at': replay['timestamp']})
    assert replay_forecast.status_code == 200
    assert 'pre-holdout' in ' '.join(replay_forecast.json()['assumptions'])
    location = stations['stations'][0]['id']
    answer = client.post('/api/explain', json={'location_id': location, 'question': 'Why is pollution high?'}).json()
    assert answer['method'] == 'grounded_template'
    assert '[SYNTHETIC]' in answer['answer']
    assert '[MODELED]' in answer['answer']


def test_cors(client):
    response = client.options('/api/stations', headers={'Origin': 'http://127.0.0.1:5173', 'Access-Control-Request-Method': 'GET'})
    assert response.headers['access-control-allow-origin'] == 'http://127.0.0.1:5173'


def test_explainer_rejects_invented_provider_number(client, monkeypatch):
    from app.services import explainer
    monkeypatch.setenv('LLM_API_KEY', 'test-only-not-a-real-key')
    class ProviderReply:
        def raise_for_status(self):
            pass
        def json(self):
            return {'choices': [{'message': {'content': '[MODELED] PM2.5 will be 99999999.'}}]}
    monkeypatch.setattr(explainer.requests, 'post', lambda *args, **kwargs: ProviderReply())
    location = client.get('/api/stations').json()['stations'][0]['id']
    result = client.post('/api/explain', json={'location_id': location, 'question': 'What happens next?'}).json()
    assert result['method'] == 'grounded_template'
    assert '99999999' not in result['answer']
