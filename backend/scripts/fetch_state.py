"""Fetch Maharashtra context; keep the last cache on provider failure."""
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
from app.services.state_data import refresh_state

if __name__ == '__main__':
    refresh_state()
    print('Maharashtra provider context refreshed; cache is gitignored.')
