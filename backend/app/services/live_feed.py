"""Public provider-published AQI indices, kept separate from PM2.5 targets."""
import json
import logging
import re
from datetime import datetime, timezone
import pandas as pd
import requests
from app.config import RAW, TIMEZONE

URL = 'https://ews.tropmet.res.in/pune/index.php'
CACHE = RAW / 'iitm_aqi.json'
NAMES = {'Shivajinagar': 'Shivajinagar, IITM', 'Bhosari': 'Bhosari, IITM',
         'Nigadi': 'Nigdi, IITM', 'katrajD': 'Katraj Dairy, MPCB',
         'sppu': 'Pune University, MPCB', 'gavali': 'Gavalinagar, MPCB',
         'wakad': 'Park Street Wakad, MPCB', 'thergaon': 'Thergaon, MPCB',
         'Pashan': 'Pashan, IITM', 'Lohgaon': 'Lohegaon, IITM',
         'Alandi': 'Alandi, IITM', 'Katraj': 'Katraj, IITM',
         'Hadapsar': 'Hadapsar, IITM', 'Bhumkar': 'Bhumkar Chowk, IITM',
         'Kothrud': 'MIT Kothrud, IITM', 'karve': 'Karve Road, MPCB'}
LOG = logging.getLogger('airtwin.feed')


def parse_indices(html, received_at=None):
    received_at = received_at or datetime.now(timezone.utc).isoformat()
    records = []
    for key, text in re.findall(r'id="(\w+)_aqi_heading"[^>]*>([^<]+)', html):
        match = re.fullmatch(r'\s*(\d{4}-\d\d-\d\d \d\d:\d\d:\d\d)\s*-\s*(\d+(?:\.\d+)?)\s*', text)
        if not match or key not in NAMES:
            continue
        value = float(match[2])
        # The upstream uses zero for several unavailable stations. Do not report it as clean air.
        if not 0 < value <= 1000:
            continue
        stamp = pd.Timestamp(match[1]).tz_localize(TIMEZONE)
        if stamp > pd.Timestamp(received_at) + pd.Timedelta(minutes=15):
            continue
        records.append({'id': 'iitm-aqi-' + key, 'name': NAMES[key], 'indicator': 'AQI',
                        'value': value, 'unit': 'index', 'timestamp': stamp.isoformat(),
                        'received_at': received_at, 'source_type': 'observed',
                        'provider': 'IITM Pune public station AQI', 'source_url': URL})
    if not records:
        raise ValueError('IITM page contained no valid station AQI records')
    return records


def refresh_indices():
    response = requests.get(URL, timeout=30)
    response.raise_for_status()
    received = datetime.now(timezone.utc).isoformat()
    records = parse_indices(response.text, received)
    payload = {'checked_at': received, 'records': records}
    CACHE.parent.mkdir(parents=True, exist_ok=True)
    temp = CACHE.with_suffix('.tmp')
    temp.write_text(json.dumps(payload, allow_nan=False))
    temp.replace(CACHE)
    return payload


def feed_status():
    try:
        payload = json.loads(CACHE.read_text())
    except (OSError, ValueError):
        payload = {'checked_at': None, 'records': []}
    now = pd.Timestamp.now(tz='UTC')
    records = []
    for record in payload['records']:
        age = max(0, (now - pd.Timestamp(record['timestamp'])).total_seconds() / 3600)
        records.append({**record, 'age_hours': round(age, 2),
                        'status': 'fresh' if age <= 3 else 'delayed' if age <= 24 else 'stale'})
    records.sort(key=lambda r: r['timestamp'], reverse=True)
    return {'source_type': 'observed', 'checked_at': payload['checked_at'], 'records': records,
            'fresh_count': sum(r['status'] == 'fresh' for r in records),
            'assumptions': ['Provider-published station AQI indices; these are not PM2.5 concentrations.',
                            'IITM station index aggregation is not independently verified. Zero placeholders are excluded.',
                            'Fresh means a measurement timestamp within three hours; older records retain their original timestamps.']}
