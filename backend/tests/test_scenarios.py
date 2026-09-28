import sys
from pathlib import Path
import pytest
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.spatial import make_grid, idw, local_weights, bearing, interpolation_anchors
from app.services.scenarios import simulate
from app.services.attribution import attribute

STATIONS = [dict(id='a', latitude=18.62, longitude=73.85, pm25=100),
            dict(id='b', latitude=18.59, longitude=73.74, pm25=30)]
TIME = pd.Timestamp('2026-01-01T08:00:00+05:30')
WEATHER = dict(relative_humidity_2m=50, precipitation=0, wind_direction_10m=270)


def test_idw_identity_and_bearing_convention():
    assert idw(18.62, 73.85, STATIONS) == 100
    assert bearing(18.6, 73.8, 18.7, 73.8) == 0
    assert bearing(18.6, 73.8, 18.6, 73.7) == 270


def test_sources_and_zero_concentration_sum_to_one():
    for value in [0, 10, 100]:
        response = attribute({**STATIONS[0], 'pm25': value}, 50, WEATHER, TIME)
        assert sum(s['value'] for s in response['shares']) == pytest.approx(1)
    weights = local_weights(18.62, 73.85, 8, WEATHER)
    assert sum(weights.values()) == pytest.approx(1)


def test_zero_cuts_and_additivity_bounds():
    cells, background = make_grid(STATIONS, WEATHER, TIME)
    zero = simulate(STATIONS[0], cells, background, dict(traffic=0, industry=0, dust=0), WEATHER, TIME)
    assert all(r['reduction'] == r['exposure_benefit'] == 0 for r in zero['results'])
    response = simulate(STATIONS[0], cells, background, dict(traffic=20, industry=30, dust=30), WEATHER, TIME)
    combined = next(r for r in response['results'] if r['id'] == 'combined')
    singles = [r for r in response['results'] if r['id'] != 'combined']
    for key in ['reduction', 'exposure_benefit']:
        assert combined[key] == pytest.approx(sum(r[key] for r in singles))
    for before, after in zip(cells, combined['cells']):
        assert before['background'] <= after['pm25'] <= before['pm25']
    assert combined['reduction_low'] <= combined['reduction'] <= combined['reduction_high']


def test_exposure_sensitivity_uses_grid_population_not_selected_location():
    cells, background = make_grid(STATIONS, WEATHER, TIME)
    cuts = dict(traffic=50, industry=60, dust=70)
    for location in [STATIONS[0], {**STATIONS[0], 'pm25': 0}]:
        result = simulate(location, cells, background, cuts, WEATHER, TIME)
        for action in result['results']:
            assert action['exposure_benefit_low'] <= action['exposure_benefit'] <= action['exposure_benefit_high']
            assert action['exposure_benefit_high'] <= sum(max(c['pm25'] - c['background'], 0) * c['population'] for c in cells)
            assert action['exposure_benefit_low'] == pytest.approx(action['exposure_benefit'] * .6 / .7 * .8)
            assert action['exposure_benefit_high'] == pytest.approx(action['exposure_benefit'] * .8 / .7 * 1.2)
    zero = simulate(STATIONS[0], cells, background, dict(traffic=0, industry=0, dust=0), WEATHER, TIME)
    assert all(r['exposure_benefit_low'] == r['exposure_benefit_high'] == 0 for r in zero['results'])


def test_single_synthetic_target_produces_non_uniform_demo_grid():
    single = [dict(id='demo-centroid', latitude=18.625, longitude=73.84, pm25=63.5, source_type='synthetic')]
    anchors = interpolation_anchors(single)
    assert len(anchors) == 7
    assert anchors[0] == single[0]
    assert idw(single[0]['latitude'], single[0]['longitude'], anchors) == pytest.approx(single[0]['pm25'])
    assert single[0]['id'] == 'demo-centroid'
    cells, _ = make_grid(single, WEATHER, TIME, background_override=45)
    values = [cell['pm25'] for cell in cells]
    assert max(values) - min(values) > 10
    assert len({round(value, 1) for value in values}) > 10


def test_non_synthetic_and_multi_station_interpolation_points_are_unchanged():
    observed = [{**STATIONS[0], 'source_type': 'observed'}]
    assert interpolation_anchors(observed) == observed
    assert interpolation_anchors(STATIONS) == STATIONS
