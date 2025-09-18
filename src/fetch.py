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
    获取深圳天气数据，带缓存与重试。
    返回 DataFrame，索引为 UTC 的 pandas.DatetimeIndex，列为 temp, hum, wind, cloud。
    """
    now = datetime.utcnow()
    if os.path.exists(cache_path):
        mtime = datetime.utcfromtimestamp(os.path.getmtime(cache_path))
        if now - mtime < timedelta(minutes=cache_ttl_minutes):
            logger.info(f"使用缓存数据: {cache_path}")
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
            logger.info(f"请求天气数据: {url} (尝试 {attempt+1}/{retries})")
            resp = requests.get(url, params=params, headers=headers, timeout=30)
            resp.raise_for_status()
            data = resp.json()
            break
        except Exception as e:
            logger.warning(f"请求失败: {e}")
            if attempt < retries - 1:
                sleep_time = 2 ** attempt
                logger.info(f"{sleep_time}s 后重试...")
                time.sleep(sleep_time)
            else:
                if os.path.exists(cache_path):
                    logger.warning("使用旧缓存数据。")
                    return pd.read_parquet(cache_path, engine=PARQUET_ENGINE)
                else:
                    logger.error("无法获取天气数据且无缓存。")
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
    logger.info(f"数据已保存到缓存: {cache_path}")
    return df
