import os
import time
import logging
from datetime import datetime, timedelta
import pandas as pd
import requests

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')

PARQUET_ENGINE = None
for engine in ("pyarrow", "fastparquet"):
    try:
        __import__(engine)
        PARQUET_ENGINE = engine
        break
    except ImportError:
        continue
if PARQUET_ENGINE is None:
    raise ImportError("Either 'pyarrow' or 'fastparquet' must be installed.")

def fetch_weather(
    lat: float,
    lon: float,
    past_days: int = 5,
    forecast_days: int = 1,
    cache_path: str = "data/weather_shenzhen.parquet",
    cache_ttl_minutes: int = 60
) -> "pd.DataFrame":
    """
    Fetch Shenzhen weather data, with caching and retry.
    Returns a DataFrame indexed by UTC pandas.DatetimeIndex, columns: temp, hum, wind, cloud.
    """
    now = datetime.utcnow()
    if os.path.exists(cache_path):
        mtime = datetime.utcfromtimestamp(os.path.getmtime(cache_path))
        if now - mtime < timedelta(minutes=cache_ttl_minutes):
            logger.info(f"Using cached data: {cache_path}")
            return pd.read_parquet(cache_path, engine=PARQUET_ENGINE)

    url = "https://api.open-meteo.com/v1/forecast"
    params = {
        "latitude": lat,
        "longitude": lon,
        "past_days": past_days,
        "forecast_days": forecast_days,
        "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover",
        # "hourly": "temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover,wind_direction_10m",
        "timezone": "UTC"
    }
    headers = {"User-Agent": "SZWeatherArt/1.0"}
    retries = 3
    for attempt in range(retries):
        try:
            logger.info(f"Requesting weather data: {url} (attempt {attempt+1}/{retries})")
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            logger.warning(f"Request failed: {e}")
            if attempt < retries - 1:
                sleep_time = 2 ** attempt
                logger.info(f"Retrying in {sleep_time}s ...")
                time.sleep(sleep_time)
            else:
                if os.path.exists(cache_path):
                    logger.warning("Using old cached data.")
                    return pd.read_parquet(cache_path, engine=PARQUET_ENGINE)
                else:
                    logger.error("Unable to fetch weather data and no cache available.")
                    raise

    hourly = data.get("hourly", {})
    times = hourly.get("time", [])
    df = pd.DataFrame({
        "time": times,
        "temp": hourly.get("temperature_2m", []),
        "hum": hourly.get("relative_humidity_2m", []),
        "wind": hourly.get("wind_speed_10m", []),
        "cloud": hourly.get("cloud_cover", []),
        # "wind_dir": hourly.get("wind_direction_10m", []),
    })
    df["time"] = pd.to_datetime(df["time"], utc=True)
    df = df.set_index("time")
    for col in ["temp", "hum", "wind", "cloud"]:
        df[col] = pd.to_numeric(df[col], errors="coerce")
    df = df.dropna().sort_index()
    os.makedirs(os.path.dirname(cache_path), exist_ok=True)
    df.to_parquet(cache_path, engine=PARQUET_ENGINE)
    logger.info(f"Data saved to cache: {cache_path}")
    return df
