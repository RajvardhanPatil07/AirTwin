import json
import pandas as pd
import pytest
import requests
from app.services import live_feed


def test_bad_station_date_does_not_discard_valid_stations():
    html = '<p id="Bhosari_aqi_heading">2026-99-10 12:00:00 - 134</p><p id="Nigadi_aqi_heading">2026-10-10 12:00:00 - 144</p>'
    records = live_feed.parse_indices(html, '2026-10-10T07:00:00Z')
    assert [r['name'] for r in records] == ['Nigdi, IITM']


def test_failed_refresh_retains_successful_fetch_and_measurement_times(tmp_path, monkeypatch):
    cache = tmp_path / 'feed.json'
    previous = {'checked_at': '2026-10-10T07:00:00Z', 'records': live_feed.parse_indices(
        '<p id="Bhosari_aqi_heading">2026-10-10 12:00:00 - 134</p>', '2026-10-10T07:00:00Z')}
    cache.write_text(json.dumps(previous))
    monkeypatch.setattr(live_feed, 'CACHE', cache)
    def fail(*args, **kwargs):
        raise requests.Timeout('provider unavailable')
    monkeypatch.setattr(live_feed.requests, 'get', fail)
    with pytest.raises(requests.Timeout):
        live_feed.refresh_indices()
    assert json.loads(cache.read_text()) == previous


def test_freshness_uses_measurement_time_and_excludes_three_hour_boundary(tmp_path, monkeypatch):
    now = pd.Timestamp('2026-10-10T12:00:00Z')
    records = []
    for key, stamp in [('Bhosari', '2026-10-10 15:00:00'), ('Nigadi', '2026-10-10 14:30:00'), ('Shivajinagar', '2026-10-08 12:00:00')]:
        records.extend(live_feed.parse_indices(f'<p id="{key}_aqi_heading">{stamp} - 134</p>', now.isoformat()))
    cache = tmp_path / 'feed.json'
    cache.write_text(json.dumps({'checked_at': now.isoformat(), 'records': records}))
    monkeypatch.setattr(live_feed, 'CACHE', cache)
    monkeypatch.setattr(live_feed.pd.Timestamp, 'now', lambda **kwargs: now)
    result = live_feed.feed_status()
    assert result['fresh_count'] == 1
    assert [r['status'] for r in result['records']] == ['fresh', 'delayed', 'stale']
    assert result['checked_at'] == now.isoformat()
