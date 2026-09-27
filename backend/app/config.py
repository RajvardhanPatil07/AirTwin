from pathlib import Path
import os
from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parents[2]
load_dotenv(ROOT / ".env")
RAW = ROOT / "data/raw"
PROCESSED = ROOT / "data/processed"
SAMPLE = ROOT / "data/sample/dataset_sample.csv"
TIMEZONE = "Asia/Kolkata"
BBOX = (73.70, 18.45, 73.98, 18.80)  # west, south, east, north
CENTROID = (18.625, 73.84)
MIN_OBSERVED_HOURS = int(os.getenv("MIN_OBSERVED_HOURS", "720"))
CITY_GRID_SIZE = int(os.getenv("CITY_GRID_SIZE", "48"))
STATION_RECENCY_HALF_LIFE_HOURS = float(os.getenv("STATION_RECENCY_HALF_LIFE_HOURS", "6"))
WEATHER_COLUMNS = ["temperature_2m", "relative_humidity_2m", "wind_speed_10m",
                   "wind_direction_10m", "precipitation"]
