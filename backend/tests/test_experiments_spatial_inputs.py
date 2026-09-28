import sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.services.experiments import chronological_blocks, conformal_radius, row_digest, verify_reference
from app.services.local_moran import benjamini_hochberg, local_moran
from app.services.spatial_inputs import aggregate_pixels, load_spatial_inputs
from app.services.spatial import make_grid
from app.services.scenarios import simulate


def test_fold_embargo_and_paired_row_identity():
    hours = pd.date_range('2025-01-01', periods=1200, freq='h', tz='Asia/Kolkata')
    rows = pd.DataFrame({'station_id': 's1', 'issue_time': hours,
        'timestamp': hours + pd.Timedelta(hours=24)})
    blocks = chronological_blocks(rows, hours[1000], hours[1100])
    assert blocks is not None
    fit, selection, calibration, test = blocks
    assert fit.timestamp.max() < selection.issue_time.min() - pd.Timedelta(hours=48)
    assert selection.timestamp.max() < calibration.issue_time.min() - pd.Timedelta(hours=48)
    assert calibration.timestamp.max() < test.issue_time.min() - pd.Timedelta(hours=48)
    assert row_digest(test) == row_digest(test.copy())
    altered = test.copy()
    altered.loc[altered.index[0], 'station_id'] = 's2'
    assert row_digest(test) != row_digest(altered)


def test_conformal_order_statistic_and_reproduction_failure():
    actual = np.array([1., 2., 3., 4.])
    predicted = np.ones(4)
    assert conformal_radius(actual, predicted, .25) == pytest.approx(np.log(4))
    with pytest.raises(ValueError):
        conformal_radius(actual[:1], predicted[:1], .1)
    assert not verify_reference({'metric': 1., 'rows': ['a']}, {'metric': 1. + 1e-9, 'rows': ['a']})
    assert verify_reference({'metric': 1., 'rows': ['a']}, {'metric': 1.1, 'rows': ['b']})


def test_population_area_allocation_conserves_counts():
    counts, fractional = aggregate_pixels([((0., 0., 2., 1.), 101.)], (0., 0., 2., 1.), 2)
    assert len(counts) == 4
    assert sum(counts) == 101
    assert fractional == pytest.approx(101.)
    assert max(counts) - min(counts) <= 1
    counts, fractional = aggregate_pixels([((0., 0., 2., 1.), 80.)], (0., 0., 1., 1.), 2)
    assert sum(counts) == 40
    assert fractional == pytest.approx(40.)


def test_bundled_spatial_inputs_provenance_and_grid():
    data = load_spatial_inputs()
    assert data is not None
    assert len(data['population_counts']) == 144
    assert sum(data['population_counts']) == round(data['population_fractional_total'])
    assert data['population_source']['year'] == 2020
    assert data['zone_source']['osm_data_timestamp']
    assert data['zones']['features']
    stations = [{'id': 'a', 'latitude': 18.6, 'longitude': 73.8, 'pm25': 42.},
                {'id': 'b', 'latitude': 18.7, 'longitude': 73.9, 'pm25': 30.}]
    timestamp = pd.Timestamp('2026-09-24T22:00:00+05:30')
    cells, background = make_grid(stations, {}, timestamp, spatial_inputs=data)
    assert sum(cell['population'] for cell in cells) == sum(data['population_counts'])
    assert all(cell['population_source_type'] == 'modeled' for cell in cells)
    assert all('WorldPop 2020' in ' '.join(cell['assumptions']) for cell in cells)
    action = simulate(stations[0], cells, background, {'traffic': 20, 'industry': 30, 'dust': 30},
                      {}, timestamp, data['zones'])
    assert all(item['population_source_type'] == 'modeled' for item in action['results'])


def test_local_moran_is_reproducible_and_adjusts_multiple_tests():
    stations = [{'id': str(i), 'latitude': 18.5 + i * .02, 'longitude': 73.7,
        'pm25': 10. + i * 3.} for i in range(8)]
    result = local_moran(stations, permutations=99)
    assert result == local_moran(stations, permutations=99)
    assert len(result) == 8
    assert all(0 <= item['p_raw'] <= item['q_bh'] <= 1 for item in result)
    assert benjamini_hochberg([.01, .02, .8]).tolist() == pytest.approx([.03, .03, .8])
