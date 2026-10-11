import json
from pathlib import Path
import pytest
import pandas as pd
from app.services.state_data import ProviderRuntime, PuneRuntime, SAMPLE, AIR_FIELDS, WEATHER_FIELDS
from app.services.regions import inside_pune
from app.services.explainer import build_context, checked_claims

@pytest.fixture(scope='module')
def state():
    return ProviderRuntime(json.loads(SAMPLE.read_text()), sample=True)

def test_state_sample_and_boundary(state):
    assert SAMPLE.stat().st_size < 1_000_000
    response = state.stations()
    assert len(response['stations']) == 2
    assert all(p['source_type'] == 'modeled' for p in response['stations'])
    assert len(AIR_FIELDS + WEATHER_FIELDS) == 15
    assert inside_pune(18.52, 73.86)
    assert not inside_pune(28.61, 77.21)
    _, cells, _, _, _ = state.snapshot()
    assert cells and all(inside_pune(c['latitude'], c['longitude']) for c in cells)

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
    attribution = state.attribution(location)
    assert attribution['source_type'] == 'modeled'
    assert len(attribution['shares']) == 4


def test_pune_live_runtime_labels_provider_data_and_keeps_validation_separate():
    payload = json.loads(SAMPLE.read_text())
    payload['points'] = payload['points']
    live = PuneRuntime(payload)
    response = live.stations()
    assert response['region']['id'] == 'pcmc'
    assert response['region']['forecast_provider'] == 'CAMS via Open-Meteo'
    assert response['coverage']['modeled_points'] == 2
    assert all(station['source_type'] == 'modeled' for station in response['stations'])
    location_id = response['stations'][0]['id']
    assert live.forecast(location_id, 24)['shap'] is None
    assert live.backtest(location_id)['available'] is False
    assert len(live.snapshot()[1]) == 144

def test_gemini_claim_checks():
    context = {'evidence': {'forecast': {'source_type': 'modeled', 'data': {'pm25': 34.2}}}}
    valid = {'claims': [{'text': 'Forecast concentration is 34.2.', 'source_type': 'modeled', 'evidence_ids': ['forecast']}]}
    assert checked_claims(valid, context) == valid['claims']
    with pytest.raises(ValueError):
        checked_claims({'claims': [{**valid['claims'][0], 'source_type': 'observed'}]}, context)
    with pytest.raises(ValueError):
        checked_claims({'claims': [{**valid['claims'][0], 'text': 'Concentration is 9999.'}]}, context)


def test_state_explanation_keeps_selected_evidence_without_full_station_payload(state):
    context = build_context(state, state.stations()['stations'][0]['id'])
    assert context['evidence']['stations']['data']['count'] == 2
    assert 'pollutants' in context['evidence']['baseline']['data']
    assert len(json.dumps(context).encode()) < 25_000


def test_provider_cache_saves_locally_without_postgres(tmp_path, monkeypatch):
    from app.services import state_data
    monkeypatch.setattr(state_data.database, 'configured', lambda: False)
    def unexpected_database_write(*args):
        pytest.fail('Unconfigured PostgreSQL must not receive snapshot writes')
    monkeypatch.setattr(state_data.database, 'save_snapshot', unexpected_database_write)
    payload = {'updated_at': '2026-10-10T11:00:00+00:00', 'points': []}
    target = tmp_path / 'provider.json'
    state_data.save_context(payload, path=target)
    assert json.loads(target.read_text()) == payload


def test_explanation_tracks_selected_pollutant_and_action_scope(state):
    location = state.stations()['stations'][0]
    context = build_context(state, location['id'], metric='pm10')
    selected = context['evidence']['selected_metric']
    assert selected['data']['metric'] == 'pm10'
    assert selected['data']['reading'] == location['pollutants']['pm10']
    assert selected['data']['display_time'].endswith('IST')
    assert 'PM2.5 only' in selected['data']['limitation']
    assert 'not measured local causes' in context['evidence']['action_guidance']['data']['status']
    missing = build_context(state, location['id'], metric='co2')
    assert missing['evidence']['selected_metric']['data']['reading'] is None


def test_action_answer_keeps_evidence_checks_and_numbers_only_steps():
    from app.services.explainer import response_for
    context = {'evidence': {'baseline': {'source_type': 'modeled', 'data': {'pm25': 34.2}},
                           'action_guidance': {'source_type': 'modeled', 'data': {'advice': 'Request a local inspection.'}}}}
    candidate = {'claims': [
        {'kind': 'finding', 'text': 'The modeled PM2.5 reading is 34.2 µg/m³.', 'source_type': 'modeled', 'evidence_ids': ['baseline']},
        {'kind': 'conclusion', 'text': 'This model alone cannot identify a local source.', 'source_type': 'modeled', 'evidence_ids': ['baseline']},
        {'kind': 'action', 'text': 'Ask local officials to inspect visible smoke.', 'source_type': 'modeled', 'evidence_ids': ['action_guidance']},
        {'kind': 'action', 'text': 'Check readings before and after any pilot.', 'source_type': 'modeled', 'evidence_ids': ['action_guidance']},
    ]}
    claims = checked_claims(candidate, context)
    answer = response_for(claims, 'gemini_evidence_checked', 'test-model', context, 'Model assumptions apply.')
    assert '\n\n1. Ask local officials' in answer['answer']
    assert '\n\n2. Check readings' in answer['answer']
    assert '[MODELED]' not in answer['answer']
    candidate['claims'][2]['text'] = 'This will reduce PM2.5 by 99%.'
    with pytest.raises(ValueError, match='numbers outside'):
        checked_claims(candidate, context)
    candidate['claims'][2]['text'] = 'Ask for an inspection.'
    candidate['claims'][2]['kind'] = 'execute'
    with pytest.raises(ValueError, match='kind'):
        checked_claims(candidate, context)


def test_readable_local_clock_is_supported_by_selected_evidence():
    context = {'evidence': {'selected_metric': {'source_type': 'modeled', 'data': {
        'value': 61.5, 'timestamp': '2026-10-11T04:00:00+05:30',
        'display_time': '11 Oct 2026, 04:00 AM IST'}}}}
    candidate = {'claims': [{'kind': 'finding', 'text': 'PM10 was 61.5 µg/m³ on October 11, 2026, at 4:00 AM.',
                             'source_type': 'modeled', 'evidence_ids': ['selected_metric']}]}
    assert checked_claims(candidate, context)
    candidate['claims'][0]['text'] = 'PM10 was 99.9 µg/m³ at 4:00 AM.'
    with pytest.raises(ValueError, match='numbers outside'):
        checked_claims(candidate, context)


def test_provider_forecast_rejects_a_missing_target_hour(state):
    from fastapi import HTTPException
    location = state.stations()['stations'][0]['id']
    original = state.all_frame
    target = state.origin + pd.Timedelta(hours=2)
    try:
        state.all_frame = original[~((original.station_id == location) & (original.timestamp == target))]
        with pytest.raises(HTTPException) as error:
            state.forecast(location, 24)
        assert error.value.status_code == 503
    finally:
        state.all_frame = original


def test_provider_timeline_publishes_available_long_horizons(state):
    timeline = state.timeline()
    assert {0, 24, 48, 72}.issubset({frame['hour'] for frame in timeline['frames']})
    station = state.stations()['stations'][0]
    future = {point['timestamp']: point['predicted'] for point in state.forecast(station['id'], 72)['series'] if point['predicted'] is not None}
    for frame in timeline['frames']:
        if frame['hour']:
            point = next(point for point in frame['stations'] if point['id'] == station['id'])
            assert point['pm25'] == future[frame['timestamp']]


def test_grid_cell_forecast_matches_spatial_timeline(state):
    timeline = state.timeline()
    cells = state.snapshot()[1]
    for cell in (cells[0], cells[len(cells) // 2], cells[-1]):
        result = state.forecast(cell['id'], 72)
        future = {p['timestamp']: p['predicted'] for p in result['series'] if p['predicted'] is not None}
        assert result['history_reference'] == cell['id']
        for frame in timeline['frames']:
            if frame['hour']:
                value = next(p['pm25'] for p in frame['cells'] if p['id'] == cell['id'])
                assert future[frame['timestamp']] == pytest.approx(value)


def test_grid_cell_forecast_rejects_invalid_spatial_anchor(state):
    from fastapi import HTTPException
    cell = state.snapshot()[1][0]
    nearest = state.location(cell['id'])[-1]
    other = next(point for point in state.points if point != nearest)
    original = state.all_frame
    try:
        state.all_frame = original.copy()
        target = (state.all_frame.station_id == other) & (state.all_frame.timestamp == state.origin + pd.Timedelta(hours=2))
        state.all_frame.loc[target, 'pm25'] = float('inf')
        with pytest.raises(HTTPException) as error:
            state.forecast(cell['id'], 24)
        assert error.value.status_code == 503
    finally:
        state.all_frame = original


def test_spatial_timeline_retains_available_shorter_forecast(state, monkeypatch):
    from fastapi import HTTPException
    original = state.forecast
    def shorter_only(location, hours, replay_at=None):
        if hours > 24:
            raise HTTPException(503, 'Provider horizon exhausted')
        return original(location, hours, replay_at)
    state.timelines.clear()
    monkeypatch.setattr(state, 'forecast', shorter_only)
    try:
        result = state.timeline()
        assert [frame['hour'] for frame in result['frames']] == [0, 3, 6, 9, 12, 18, 24]
    finally:
        state.timelines.clear()


def test_explanation_action_audience(state):
    context = build_context(state, state.stations()['stations'][0]['id'])
    claim = {'kind': 'action', 'audience': 'municipality',
             'text': 'Request an inspection of visible dust.',
             'source_type': 'modeled', 'evidence_ids': ['action_guidance']}
    assert checked_claims({'claims': [claim]}, context)[0]['audience'] == 'municipality'
    with pytest.raises(ValueError, match='Invalid action audience'):
        checked_claims({'claims': [{**claim, 'audience': 'unknown'}]}, context)


def test_model_reference_identity_is_per_pollutant_and_complete_series():
    from copy import deepcopy
    payload = json.loads(SAMPLE.read_text())
    original = payload['points'][0]
    duplicate = deepcopy(original)
    duplicate.update(id='shared-reference', name='Shared area', longitude=original['longitude'] + .01)
    independent = deepcopy(original)
    independent.update(id='different-reference', name='Other area', longitude=original['longitude'] + .02)
    independent['air']['pm10'][0] += 1
    payload['points'] = [original, duplicate, independent]
    stations = ProviderRuntime(payload, sample=True).stations()['stations']
    assert len({station['model_reference_id'] for station in stations}) == 1
    assert stations[0]['pollutants']['pm10']['model_reference_id'] == stations[1]['pollutants']['pm10']['model_reference_id']
    assert stations[0]['pollutants']['pm10']['model_reference_id'] != stations[2]['pollutants']['pm10']['model_reference_id']


def test_monitor_measurement_time_overrides_stale_location_metadata(monkeypatch):
    from app.services import state_data
    import requests
    now = pd.Timestamp.now(tz='UTC')
    locations = [{'id': i, 'name': f'Monitor {i}', 'coordinates': {'latitude': 18.52, 'longitude': 73.86},
                  'datetimeLast': {'utc': (now-pd.Timedelta(days=10)).isoformat()},
                  'sensors': [{'id': i, 'parameter': {'name': 'pm25', 'units': 'µg/m³'}}]} for i in (1, 2)]
    def fetch(url, *args):
        if '/1/' in url:
            raise requests.Timeout()
        return {'results': [{'sensorsId': 2, 'value': 32, 'datetime': {'utc': (now-pd.Timedelta(hours=1)).isoformat()}},
                            {'sensorsId': 2, 'value': 99, 'datetime': {'utc': (now-pd.Timedelta(hours=25)).isoformat()}},
                            {'sensorsId': 2, 'value': 55, 'datetime': {'utc': (now+pd.Timedelta(hours=1)).isoformat()}},
                            {'sensorsId': 2, 'value': float('nan'), 'datetime': {'utc': now.isoformat()}}]}
    monkeypatch.setattr(state_data, 'get_payload', fetch)
    records, failures = state_data.fetch_observed_locations(locations, 'test', now)
    assert failures == 1
    assert len(records) == 1
    assert records[0]['pm25'] == 32
    assert pd.Timestamp(records[0]['timestamp']) == now-pd.Timedelta(hours=1)
    assert records[0]['source_type'] == 'observed'


def test_provider_grid_aliases_do_not_weight_interpolation_twice(monkeypatch):
    from app.services import state_data
    payload = json.loads(SAMPLE.read_text())
    for point in payload['points']:
        point['air_grid'] = {'latitude': point['latitude'], 'longitude': point['longitude']}
    clone = {**payload['points'][0], 'id': 'alias', 'name': 'Another area', 'latitude': 18.6}
    payload['points'].append(clone)
    runtime = ProviderRuntime(payload, sample=True)
    original = state_data.make_grid
    captured = []
    def capture(points, *args, **kwargs):
        captured.extend(points)
        return original(points, *args, **kwargs)
    monkeypatch.setattr(state_data, 'make_grid', capture)
    stations, cells, *_ = runtime.snapshot()
    assert len(stations) == 3
    assert len(captured) == 2
    assert cells[0]['measurement_support']['nearest_monitor_km'] is None
    assert cells[0]['measurement_support']['synchronized_monitor_count'] == 0
    assert 'not been validated' in cells[0]['measurement_support']['uncertainty']


def test_only_same_hour_measurements_enter_modeled_surface(monkeypatch):
    from app.services import state_data
    payload = json.loads(SAMPLE.read_text())
    clock = pd.Timestamp(payload['sample_origin'])
    payload['observed'] = [
        {'id': f'openaq-{i}', 'name': str(i), 'short_name': str(i), 'latitude': 18.52,
         'longitude': 73.86, 'pm25': 90, 'timestamp': (clock-pd.Timedelta(hours=age)).isoformat(),
         'source_type': 'observed', 'assumptions': []} for i, age in [(1, 0), (2, 4), (3, 25)]]
    monkeypatch.setattr(pd.Timestamp, 'now', lambda tz=None: clock.tz_convert(tz or 'UTC'))
    runtime = ProviderRuntime(payload, sample=True)
    captured = []
    original = state_data.make_grid
    def capture(points, *args, **kwargs):
        captured.extend(points)
        return original(points, *args, **kwargs)
    monkeypatch.setattr(state_data, 'make_grid', capture)
    stations, cells, *_ = runtime.snapshot()
    assert {p['id'] for p in stations if p['source_type'] == 'observed'} == {'openaq-1', 'openaq-2'}
    assert [p['id'] for p in captured if p['source_type'] == 'observed'] == ['openaq-1']
    assert cells[0]['source_type'] == 'modeled'
    assert cells[0]['measurement_support']['synchronized_monitor_count'] == 1
    assert cells[0]['measurement_support']['nearest_monitor_km'] is not None
