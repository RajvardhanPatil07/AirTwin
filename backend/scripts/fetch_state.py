"""Fetch Maharashtra context; keep the last cache on provider failure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
import requests
from fastapi import HTTPException
from app.services.state_data import refresh_state, get_state_runtime

if __name__ == '__main__':
    try:
        refresh_state()
        print('Maharashtra provider context refreshed; cache is gitignored.')
    except (requests.RequestException, ValueError, KeyError, TypeError, HTTPException):
        runtime = get_state_runtime()
        print(f'WARNING: Live provider fetch failed. Retaining labeled cache/sample dated {runtime.origin.isoformat()}.')
