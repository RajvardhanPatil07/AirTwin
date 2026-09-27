"""Shared bounded HTTP retries and explicit offline fallback."""
import logging
import sys
import time
from pathlib import Path
import pandas as pd
import requests

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.config import SAMPLE, TIMEZONE

logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")
LOG = logging.getLogger("airtwin")

def get_json(url, params, headers=None):
    for attempt in range(4):
        try:
            response = requests.get(url, params=params, headers=headers, timeout=45)
            if response.status_code == 429 or response.status_code >= 500:
                # Cap Retry-After so a rate-limited demo cannot hang indefinitely.
                try:
                    delay = min(float(response.headers.get("Retry-After", 2 ** attempt)), 60)
                except ValueError:
                    delay = 2 ** attempt
                time.sleep(max(delay, 0))
                continue
            response.raise_for_status()
            return response.json()
        except (requests.RequestException, ValueError):
            if attempt == 3:
                raise
            time.sleep(2 ** attempt)
    raise RuntimeError(f"API retries exhausted: {url}")

def pages(url, params, headers):
    page = 1
    while True:
        payload = get_json(url, {**params, "limit": 1000, "page": page}, headers)
        rows = payload.get("results", [])
        if not rows:
            break
        yield from rows
        found = payload.get("meta", {}).get("found")
        if len(rows) < 1000 or (isinstance(found, int) and page * 1000 >= found):
            break
        page += 1

def sample_frame():
    frame = pd.read_csv(SAMPLE)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"], utc=True).dt.tz_convert(TIMEZONE)
    LOG.warning("Using committed SYNTHETIC demo sample; this is not station observation data.")
    return frame
