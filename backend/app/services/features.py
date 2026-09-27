"""Issue-time features on a complete hourly axis; target shifts are separate."""
import numpy as np
import pandas as pd
from app.config import WEATHER_COLUMNS, TIMEZONE

LAGS = (1, 2, 3, 6, 12, 24, 48)


def hourly(frame):
    frame = frame.copy()
    frame['timestamp'] = pd.to_datetime(frame.timestamp, utc=True).dt.tz_convert(TIMEZONE)
    frame = frame.sort_values('timestamp').drop_duplicates('timestamp').set_index('timestamp')
    return frame.reindex(pd.date_range(frame.index.min(), frame.index.max(), freq='h'))


def exogenous_at(exog, column, times):
    if exog is None or column not in exog:
        return np.full(len(times), np.nan)
    return exog[column].reindex(times).to_numpy(dtype=float)


def build_features(frame, horizon=24, exog=None):
    """exog: optional frame indexed by timestamp with boundary_layer_height and cams_pm25.

    cams_target is the CAMS value valid at the target hour. Historically this is the
    provider's archived short-lead forecast; at serving time it is the current CAMS forecast.
    """
    data = hourly(frame)
    x = pd.DataFrame(index=data.index)
    x['current_pm25'] = data.pm25
    for lag in LAGS:
        x[f'lag_{lag}'] = data.pm25.shift(lag)
    for window in (6, 24):
        past = data.pm25.shift(1).rolling(window, min_periods=window)
        x[f'rolling_mean_{window}'] = past.mean()
        x[f'rolling_std_{window}'] = past.std()
    target_time = x.index + pd.Timedelta(hours=horizon)
    for name, values, period in [('hour', target_time.hour, 24),
                                  ('dow', target_time.dayofweek, 7),
                                  ('month', target_time.month, 12)]:
        x[name] = values
        x[f'{name}_sin'] = np.sin(2 * np.pi * values / period)
        x[f'{name}_cos'] = np.cos(2 * np.pi * values / period)
    x['winter'] = np.isin(target_time.month, [11, 12, 1]).astype(int)
    for column in WEATHER_COLUMNS:
        x[column] = pd.to_numeric(data.get(column, pd.Series(np.nan, index=data.index)), errors='coerce')
        # Archived issue-time forecasts may be supplied; never shift realized weather forward.
        forecast = data.get(f'forecast_{horizon}_{column}', x[column])
        x[f'horizon_{column}'] = forecast.fillna(x[column])
    x['boundary_layer_height'] = exogenous_at(exog, 'boundary_layer_height', x.index)
    x['cams_issue'] = exogenous_at(exog, 'cams_pm25', x.index)
    x['cams_target'] = exogenous_at(exog, 'cams_pm25', target_time)
    radians = np.deg2rad(x.wind_direction_10m)
    x['wind_u'] = -x.wind_speed_10m * np.sin(radians)
    x['wind_v'] = -x.wind_speed_10m * np.cos(radians)
    x['calm_humid'] = ((x.wind_speed_10m < 2) & (x.relative_humidity_2m > 70)).astype(int)
    x['latitude'] = data.latitude.ffill()
    x['longitude'] = data.longitude.ffill()
    return x


def supervised(frame, horizon, exog=None):
    rows = []
    for station_id, station in frame.groupby('station_id'):
        data = hourly(station)
        x = build_features(station, horizon, exog)
        x['target'] = data.pm25.shift(-horizon)
        x['persistence'] = data.pm25
        x['issue_time'] = x.index
        x['timestamp'] = x.index + pd.Timedelta(hours=horizon)
        x['station_id'] = str(station_id)
        x['source_type'] = data.source_type.shift(-horizon)
        required = ['target', 'current_pm25', *[f'lag_{lag}' for lag in LAGS], 'rolling_mean_24']
        rows.append(x.dropna(subset=required).reset_index(drop=True))
    return pd.concat(rows, ignore_index=True).sort_values(['issue_time', 'station_id']).reset_index(drop=True)


def group_for(feature):
    if feature.startswith(('lag_', 'rolling_', 'current_')):
        return 'persistence'
    if feature.startswith(('hour', 'dow', 'month', 'winter')):
        return 'temporal'
    if feature.startswith('cams_'):
        return 'cams'
    if feature in ('latitude', 'longitude'):
        return 'spatial'
    return 'weather'
