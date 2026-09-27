import sys
from pathlib import Path
import pytest
import pandas as pd
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.spatial import make_grid, idw, local_weights, bearing
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


def test_idw_downweights_stale_station():
    fresh = dict(id='fresh', latitude=18.60, longitude=73.80, pm25=40, age_hours=0)
    stale = dict(id='stale', latitude=18.60, longitude=73.82, pm25=160, age_hours=18)
    midpoint = idw(18.60, 73.81, [fresh, stale])
    assert midpoint < 100


def test_city_grid_is_dense():
    cells, _ = make_grid(STATIONS, WEATHER, TIME)
    assert len(cells) == 48 * 48
