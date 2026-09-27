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
    assert combined['reduction'] > 0
    assert combined['after'] < combined['before']
    assert combined['exposure_benefit'] > 0
    grid = client.get('/api/hotspots', params={'mode': 'after', 'scenario_id': scenario['scenario_id']}).json()
    assert grid['cells'] == combined['cells']
    assert client.post('/api/scenarios', json={'location_id': location, 'cuts': {'traffic': -1, 'industry': 0, 'dust': 0}}).status_code == 422
    assert client.get('/api/hotspots?mode=after&scenario_id=missing').status_code == 404
    assert client.get('/api/forecast?location_id=missing').status_code == 404
    assert client.get(f'/api/forecast?location_id={location}&hours=100').status_code == 422


def test_replay_and_gemini_requires_key(client, monkeypatch):
    monkeypatch.delenv('GEMINI_API_KEY', raising=False)
    replay = client.get('/api/replay').json()
    stations = client.get('/api/stations', params={'replay_at': replay['timestamp']}).json()
    assert stations['data_mode'] == 'historical_replay'
    replay_forecast = client.get('/api/forecast', params={'location_id': replay['location_id'], 'replay_at': replay['timestamp']})
    assert replay_forecast.status_code == 200
    assert 'pre-holdout' in ' '.join(replay_forecast.json()['assumptions'])
    location = stations['stations'][0]['id']
    answer = client.post('/api/explain', json={'location_id': location, 'question': 'Why is pollution high?'})
    assert answer.status_code == 200
    body = answer.json()
    assert body['method'] == 'grounded_summary'
    assert 'GEMINI_API_KEY missing' in body['assumptions'][0]
    assert all(claim['evidence_ids'] for claim in body['claims'])


@pytest.mark.parametrize('origin', ['http://127.0.0.1:5173', 'http://127.0.0.1:5188', 'http://localhost:5188'])
def test_cors(client, origin):
    response = client.options('/api/stations', headers={'Origin': origin, 'Access-Control-Request-Method': 'GET'})
    assert response.headers['access-control-allow-origin'] == origin


def test_unavailable_gemini_model_is_not_reported_as_rejected_key(monkeypatch):
    from app.services import explainer
    from fastapi import HTTPException
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-not-a-real-key')
    monkeypatch.setenv('GEMINI_MODEL', 'retired-model')
    class Reply:
        status_code = 404
    monkeypatch.setattr(explainer.requests, 'post', lambda *args, **kwargs: Reply())
    with pytest.raises(HTTPException) as error:
        explainer.gemini_claims('key', 'retired-model', {'evidence': {}}, 'Why?', [])
    assert error.value.status_code == 503
    assert 'retired-model is unavailable' in error.value.detail
    assert 'GEMINI_MODEL' in error.value.detail


def test_explainer_rejects_invented_provider_number(client, monkeypatch):
    from app.services import explainer
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-not-a-real-key')
    class ProviderReply:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {'candidates': [{'content': {'parts': [{'text': '{"claims":[{"text":"PM2.5 will be 99999999","source_type":"modeled","evidence_ids":["forecast"]}]}'}]}}]}
    monkeypatch.setattr(explainer.requests, 'post', lambda *args, **kwargs: ProviderReply())
    location = client.get('/api/stations').json()['stations'][0]['id']
    result = client.post('/api/explain', json={'location_id': location, 'question': 'What happens next?'})
    assert result.status_code == 200
    assert result.json()['method'] == 'grounded_summary'
    assert '99999999' not in result.json()['answer']


def test_number_check_accepts_rounding_and_units_but_rejects_inventions():
    from app.services.explainer import checked_claims
    context = {'evidence': {'forecast': {'source_type': 'modeled', 'data': {'pm25': 39.9437, 'share': 0.3123, 'benefit': 304821.4}}}}
    ok = {'claims': [{'text': 'PM2.5 falls to 39.9 µg/m³ (31%), benefit 304.8K person·µg/m³', 'source_type': 'modeled', 'evidence_ids': ['forecast']}]}
    assert checked_claims(ok, context)
    bad = {'claims': [{'text': 'PM2.5 will be 71.2 µg/m³', 'source_type': 'modeled', 'evidence_ids': ['forecast']}]}
    with pytest.raises(ValueError):
        checked_claims(bad, context)


def test_gemini_uses_actual_context_and_applied_cuts(client, monkeypatch):
    import json
    from app.services import explainer
    monkeypatch.setenv('GEMINI_API_KEY', 'test-only-not-a-real-key')
    captured = {}
    class Reply:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            claim = {'text': 'This forecast is modeled, and source shares are proxy estimates.',
                     'source_type': 'modeled', 'evidence_ids': ['forecast', 'attribution']}
            return {'candidates': [{'content': {'parts': [{'text': json.dumps({'claims': [claim]})}]}}]}
    def provider(url, **kwargs):
        captured.update(json.loads(kwargs['json']['contents'][0]['parts'][0]['text']))
        assert 'generativelanguage.googleapis.com' in url
        return Reply()
    monkeypatch.setattr(explainer.requests, 'post', provider)
    location = client.get('/api/stations').json()['stations'][0]['id']
    response = client.post('/api/explain', json={'location_id': location, 'question': 'Why?',
        'cuts': {'traffic': 0, 'industry': 10, 'dust': 15}, 'hours': 48,
        'history': [{'role': 'user', 'content': 'Explain the weather.'}]})
    assert response.status_code == 200, response.text
    assert response.json()['method'] == 'gemini_evidence_checked'
    assert captured['context']['evidence']['scenarios']['data']['cuts']['traffic'] == 0
    assert captured['conversation'][0]['content'] == 'Explain the weather.'


def test_provider_bare_claim_array_keeps_evidence_checks(monkeypatch):
    from app.services import explainer
    context = {'evidence': {'population': {'source_type': 'synthetic', 'data': {'population': 100}}}}
    class ProviderReply:
        status_code = 200
        def raise_for_status(self):
            pass
        def json(self):
            return {'candidates': [{'content': {'parts': [{'text': '[{"text":"Population 100 is synthetic","source_type":"synthetic","evidence_ids":["population"]}]'}]}}]}
    monkeypatch.setattr(explainer.requests, 'post', lambda *a, **kw: ProviderReply())
    assert explainer.gemini_claims('test-key', 'test-model', context, 'Explain', [])[0]['source_type'] == 'synthetic'
    context['evidence']['population']['data']['population'] = 10
    with pytest.raises(ValueError, match='numbers outside'):
        explainer.gemini_claims('test-key', 'test-model', context, 'Explain', [])
