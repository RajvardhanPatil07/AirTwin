"""Exploratory station-level Local Moran statistics on one shared observation hour."""
import math

import numpy as np

from app.services.spatial import distance_km


def benjamini_hochberg(p_values):
    p = np.asarray(p_values, dtype=float)
    order = np.argsort(p, kind='stable')
    q = np.empty(len(p), dtype=float)
    running = 1.
    for position in range(len(p) - 1, -1, -1):
        index = order[position]
        running = min(running, p[index] * len(p) / (position + 1))
        q[index] = running
    return q


def local_moran(stations, permutations=999, neighbors=3, seed=42):
    if len(stations) < max(8, neighbors + 2) or permutations < 99:
        raise ValueError('At least eight shared-hour stations and 99 permutations are required')
    stations = sorted(stations, key=lambda s: str(s['id']))
    values = np.asarray([s['pm25'] for s in stations], dtype=float)
    if not np.isfinite(values).all() or np.std(values) == 0:
        raise ValueError('Station values must be finite and nonconstant')
    z = (values - values.mean()) / values.std()
    rng = np.random.default_rng(seed)
    output = []
    for i, station in enumerate(stations):
        distance = np.asarray([distance_km(station['latitude'], station['longitude'],
            other['latitude'], other['longitude']) if i != j else math.inf
            for j, other in enumerate(stations)])
        nearest = np.argsort(distance, kind='stable')[:neighbors]
        lag = float(z[nearest].mean())
        statistic = float(z[i] * lag)
        others = np.delete(z, i)
        null = np.asarray([z[i] * others[rng.choice(len(others), size=neighbors, replace=False)].mean()
                           for _ in range(permutations)])
        p = float((1 + np.count_nonzero(np.abs(null - null.mean()) >= abs(statistic - null.mean()))) /
                  (permutations + 1))
        quadrant = ('high_high' if z[i] > 0 and lag > 0 else
                    'low_low' if z[i] < 0 and lag < 0 else
                    'high_low' if z[i] > 0 else 'low_high')
        output.append({'station_id': str(station['id']), 'station_name': station.get('name', str(station['id'])),
            'pm25': float(values[i]),
            'local_moran_i': statistic, 'standardized_pm25': float(z[i]),
            'neighbor_lag': lag, 'quadrant': quadrant,
            'neighbor_station_ids': [str(stations[j]['id']) for j in nearest], 'p_raw': p})
    for item, q in zip(output, benjamini_hochberg([item['p_raw'] for item in output])):
        item['q_bh'] = float(q)
        item['flagged_q_0_05'] = bool(q <= .05)
    return output
