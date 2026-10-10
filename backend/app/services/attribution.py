from app.services.spatial import local_weights, ASSUMPTIONS


def attribute(location, background, weather, timestamp, zones=None, assumptions=None):
    weights = local_weights(location['latitude'], location['longitude'], timestamp.hour, weather, zones)
    value = location['pm25']
    background = min(background, value)
    excess = max(value - background, 0)
    # A percentile background equal to a CAMS reference value means this
    # snapshot contains no modeled local excess to apportion. Zero shares are
    # not evidence that local sources are absent.
    resolvable = excess > max(0.05, value * 0.005)
    names = {'traffic': ('Traffic', '#0b4f6c'), 'industry': ('Industry', '#b45309'),
             'dust': ('Construction / road dust', '#6b7280')}
    shares = [{'name': name, 'value': weights[key] * excess / value if value and resolvable else 0, 'color': color}
              for key, (name, color) in names.items()]
    shares.append({'name': 'Regional background', 'value': background / value if value else 1, 'color': '#9bbdb0'})
    return {'location_id': location['id'], 'background': background, 'shares': shares,
            'status': 'estimated' if resolvable else 'unresolved',
            'status_reason': None if resolvable else 'The selected modeled concentration is effectively equal to the estimated regional background. This snapshot cannot resolve local source contributions.',
            'source_type': 'modeled', 'assumptions': assumptions or ASSUMPTIONS}
