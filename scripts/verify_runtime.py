"""Check a running API using its real data, model and explanation path."""
import argparse
import json
import math
import urllib.request


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--url', default='http://127.0.0.1:8000')
    parser.add_argument('--require-gemini', action='store_true')
    args = parser.parse_args()

    def request(path, body=None):
        payload = json.dumps(body).encode() if body is not None else None
        req = urllib.request.Request(args.url.rstrip('/') + '/api/' + path, data=payload,
                                     headers={'Content-Type': 'application/json'})
        with urllib.request.urlopen(req, timeout=180) as response:
            data = json.load(response)
        assert data['source_type'] in {'observed', 'modeled', 'synthetic'}, path
        if data['source_type'] == 'modeled':
            assert isinstance(data['assumptions'], list), path
        return data

    health = request('health')
    assert health['status'] == 'ok'
    stations = request('stations')['stations']
    assert stations
    location = stations[0]['id']
    assert request('hotspots?mode=before')['cells']
    forecast = request(f'forecast?location_id={location}&hours=24')
    assert any(point['predicted'] is not None for point in forecast['series'])
    backtest = request(f'backtest?location_id={location}')
    assert backtest['available'] and backtest['metrics']
    assert math.isclose(sum(s['value'] for s in request(f'attribution?location_id={location}')['shares']), 1)
    body = {'location_id': location, 'cuts': {'traffic': 20, 'industry': 30, 'dust': 30}}
    scenario = request('scenarios', body)
    combined = next(r for r in scenario['results'] if r['id'] == 'combined')
    singles = [r for r in scenario['results'] if r['id'] != 'combined']
    assert len(singles) == 3
    assert math.isclose(combined['exposure_benefit'], sum(r['exposure_benefit'] for r in singles), abs_tol=1e-6)
    for result in scenario['results']:
        assert result['exposure_benefit_low'] <= result['exposure_benefit'] <= result['exposure_benefit_high']
        assert result['reduction_low'] <= result['reduction'] <= result['reduction_high']
    assert request('hotspots?mode=after&scenario_id=' + scenario['scenario_id'])['cells'] == combined['cells']
    zero = request('scenarios', {**body, 'cuts': dict.fromkeys(body['cuts'], 0)})
    assert all(r['before'] == r['after'] and r['exposure_benefit'] == 0 for r in zero['results'])
    explanation = request('explain', {**body, 'question': 'Which individual action helps most, and what are the limitations?'})
    assert explanation['claims'] and all(c['evidence_ids'] for c in explanation['claims'])
    assert explanation['method'] in {'grounded_summary', 'gemini_evidence_checked'}
    if args.require_gemini:
        assert explanation['method'] == 'gemini_evidence_checked', 'Provider returned a labeled fallback; generated AI not verified.'
    print(json.dumps({'status': 'passed', 'location_id': location,
                      'target_source_types': health['target_source_types'],
                      'last_dataset_time': health['last_dataset_time'],
                      'explanation_method': explanation['method'],
                      'checks': ['health', 'stations', 'hotspots', 'forecast', 'backtest', 'attribution',
                                 'three_interventions', 'sensitivity', 'after_map', 'zero_cuts', 'explanation']}, indent=2))


if __name__ == '__main__':
    main()
