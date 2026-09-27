"""Load processed data or the labeled sample without inventing observations."""
import hashlib
import pandas as pd
from app.config import PROCESSED, RAW, SAMPLE, TIMEZONE

EXOGENOUS = RAW / 'exogenous.csv'


def load_dataset(force_sample=False):
    path = PROCESSED / 'dataset.parquet'
    warnings = []
    if force_sample or not path.exists():
        path = SAMPLE
        warnings.append('Processed dataset unavailable or offline mode: using the committed SYNTHETIC sample.')
    def read_clean(candidate):
        data = pd.read_csv(candidate) if candidate.suffix == '.csv' else pd.read_parquet(candidate)
        required = {'station_id', 'timestamp', 'source_type', 'pm25', 'latitude', 'longitude'}
        if not required <= set(data.columns):
            raise ValueError('Dataset missing required columns')
        data['station_id'] = data.station_id.astype(str)
        data['timestamp'] = pd.to_datetime(data.timestamp, utc=True, errors='coerce').dt.tz_convert(TIMEZONE)
        data['pm25'] = pd.to_numeric(data.pm25, errors='coerce')
        data = data[data.source_type.isin(['observed', 'modeled', 'synthetic']) & data.pm25.between(0, 1000)]
        data = data.dropna(subset=['timestamp', 'latitude', 'longitude'])
        if data.empty:
            raise ValueError('No valid dataset rows')
        return data.sort_values(['station_id', 'timestamp']).drop_duplicates(['station_id', 'timestamp'])

    try:
        frame = read_clean(path)
    except (OSError, ValueError, KeyError, TypeError):
        path = SAMPLE
        frame = read_clean(path)
        warnings.append('Processed dataset could not be read or validated; using the committed SYNTHETIC sample.')
    sources = set(frame.source_type)
    if 'synthetic' in sources:
        warnings.append('SYNTHETIC targets: trained model metrics do not establish real-world forecast accuracy.')
    if 'modeled' in sources:
        warnings.append('CAMS MODELED targets: this evaluates prediction of model output, not station observations.')
    return frame.reset_index(drop=True), warnings, hashlib.sha256(path.read_bytes()).hexdigest()


def load_exogenous(force_sample=False):
    """Centroid CAMS PM2.5 and boundary-layer height indexed by hour, or (None, '') if unavailable."""
    if force_sample or not EXOGENOUS.exists():
        return None, ''
    try:
        data = pd.read_csv(EXOGENOUS)
        data['timestamp'] = pd.to_datetime(data.timestamp, utc=True).dt.tz_convert(TIMEZONE)
        data = data.drop_duplicates('timestamp').set_index('timestamp').sort_index()
        for column in data:
            data[column] = pd.to_numeric(data[column], errors='coerce')
        return data, hashlib.sha256(EXOGENOUS.read_bytes()).hexdigest()
    except (OSError, ValueError, KeyError, TypeError):
        return None, ''


def load_all(force_sample=False):
    frame, warnings, fingerprint = load_dataset(force_sample)
    exog, exog_hash = load_exogenous(force_sample or 'synthetic' in set(frame.source_type))
    if exog_hash:
        fingerprint = hashlib.sha256((fingerprint + exog_hash).encode()).hexdigest()
    return frame, warnings, fingerprint, exog
