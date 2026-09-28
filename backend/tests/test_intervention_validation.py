import importlib.util
from pathlib import Path

spec = importlib.util.spec_from_file_location('intervention_validation', Path(__file__).resolve().parents[2] / 'scripts/validate_interventions.py')
module = importlib.util.module_from_spec(spec)
spec.loader.exec_module(module)


def test_independent_response_stress_finds_ranking_reversal_and_zero_cuts():
    cells = [{'pm25': 100., 'background': 20., 'population': 100.,
              'local_weights': {'traffic': 0.2, 'industry': 0.6, 'dust': 0.2}}]
    report = module.stress_rankings(cells, dict.fromkeys(['traffic', 'industry', 'dust'], 30), [1.], [0., 0.7, 1.])
    assert report['central_leader'] == 'industry'
    assert report['ranking_changed']
    assert 'dust' in report['examples'] and 'traffic' in report['examples']
    example = report['examples']['dust']
    assert example['scores']['dust'] > example['scores']['industry']
    zero = module.stress_rankings(cells, dict.fromkeys(['traffic', 'industry', 'dust'], 0), [1.], [0.7])
    assert zero['central_leader'] is None
    assert zero['winner_counts'] == {'tie_or_zero': 3}
