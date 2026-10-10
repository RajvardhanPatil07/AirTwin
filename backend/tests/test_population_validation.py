import importlib.util
from pathlib import Path
import pytest

spec = importlib.util.spec_from_file_location('population_validation', Path(__file__).resolve().parents[2] / 'scripts/validate_population.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_population_profile_can_reverse_ranking_without_changing_total():
    cells = [{'id': 'a', 'pm25': 10., 'population': 90.},
             {'id': 'b', 'pm25': 10., 'population': 10.}]
    results = [{'id': 'traffic', 'cells': [{'id': 'a', 'pm25': 5.}, {'id': 'b', 'pm25': 10.}]},
               {'id': 'industry', 'cells': [{'id': 'a', 'pm25': 10.}, {'id': 'b', 'pm25': 4.}]}]
    rows = module.population_sensitivity(cells, results)
    assert rows[0]['leading_individual'] == 'traffic'
    assert rows[1]['leading_individual'] == 'industry'
    assert rows[2]['leading_individual'] == 'industry'
    assert all(row['total_synthetic_weight'] == pytest.approx(100.) for row in rows)
