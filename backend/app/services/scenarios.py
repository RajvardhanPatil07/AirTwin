"""One additive equation drives location results and every after-grid."""
import hashlib
import json
from app.services.spatial import CONFIG, ASSUMPTIONS, local_weights

NAMES = {'traffic': 'Traffic restriction', 'industry': 'Industrial controls', 'dust': 'Dust suppression'}


def delta(value, background, weights, cuts, pass_through=None):
    pass_through = CONFIG['pass_through']['central'] if pass_through is None else pass_through
    weighted = sum(weights[key] * max(0, min(cuts[key], CONFIG['cuts_max'][key])) / 100 for key in NAMES)
    return max(value - background, 0) * weighted * pass_through


def simulate(location, cells, background, cuts, weather, timestamp, zones=None, assumptions=None):
    weights = local_weights(location['latitude'], location['longitude'], timestamp.hour, weather, zones)
    assumptions = assumptions or ASSUMPTIONS
    packages = [('combined', 'Combined clean-air package', cuts)]
    packages += [(key, name, {other: cuts[other] if other == key else 0 for other in NAMES}) for key, name in NAMES.items()]
    results = []
    for action_id, name, action_cuts in packages:
        reduction = delta(location['pm25'], background, weights, action_cuts)
        after_grid = [{**cell, 'pm25': max(cell['background'], cell['pm25'] - delta(cell['pm25'], cell['background'], cell['local_weights'], action_cuts))} for cell in cells]
        low = delta(location['pm25'], background, weights, action_cuts, CONFIG['pass_through']['low']) * (1 - CONFIG['share_sensitivity'])
        high = min(max(location['pm25'] - background, 0), delta(location['pm25'], background, weights, action_cuts, CONFIG['pass_through']['high']) * (1 + CONFIG['share_sensitivity']))
        results.append({'id': action_id, 'name': name, 'cuts': action_cuts, 'rank': 0,
                        'before': location['pm25'], 'after': location['pm25'] - reduction,
                        'reduction': reduction, 'reduction_low': low, 'reduction_high': high,
                        'reduction_percent': 100 * reduction / location['pm25'] if location['pm25'] else 0,
                        'exposure_benefit': sum((cell['pm25'] - after_grid[i]['pm25']) * cell['population'] for i, cell in enumerate(cells)),
                        'exposure_benefit_low': sum(delta(cell['pm25'], cell['background'], cell['local_weights'], action_cuts, CONFIG['pass_through']['low']) * (1 - CONFIG['share_sensitivity']) * cell['population'] for cell in cells),
                        'exposure_benefit_high': sum(min(max(cell['pm25'] - cell['background'], 0), delta(cell['pm25'], cell['background'], cell['local_weights'], action_cuts, CONFIG['pass_through']['high']) * (1 + CONFIG['share_sensitivity'])) * cell['population'] for cell in cells),
                        'population_source_type': cells[0]['population_source_type'] if cells else 'synthetic', 'cells': after_grid,
                        'source_type': 'modeled', 'assumptions': assumptions})
    results.sort(key=lambda item: -item['exposure_benefit'])
    for rank, item in enumerate(results, 1):
        item['rank'] = rank
    identity = json.dumps([location['id'], timestamp.isoformat(), cuts], sort_keys=True)
    return {'scenario_id': hashlib.sha256(identity.encode()).hexdigest()[:16],
            'location_id': location['id'], 'results': results, 'source_type': 'modeled', 'assumptions': assumptions}
