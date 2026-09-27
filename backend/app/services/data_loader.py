"""Load processed data or the labeled sample without inventing observations."""
import hashlib
import pandas as pd
from app.config import PROCESSED, SAMPLE, TIMEZONE


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
