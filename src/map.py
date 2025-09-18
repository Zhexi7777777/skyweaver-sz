import logging
import numpy as np
import pandas as pd
from scipy.ndimage import gaussian_filter1d

logger = logging.getLogger(__name__)


def normalize_series(x: "np.ndarray | pd.Series", lo: float | None = None, hi: float | None = None, clip: bool = True) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    if lo is None:
        lo = np.nanmin(x)
    if hi is None:
        hi = np.nanmax(x)
    norm = (x - lo) / (hi - lo) if hi > lo else np.zeros_like(x)
    if clip:
        norm = np.clip(norm, 0, 1)
    return norm.astype(np.float32)


def smooth_series(x: np.ndarray, sigma: float = 1.0) -> np.ndarray:
    x = np.asarray(x, dtype=np.float32)
    if np.all(np.isnan(x)):
        return np.zeros_like(x)
    x = np.nan_to_num(x, nan=np.nanmean(x))
    return gaussian_filter1d(x, sigma=sigma).astype(np.float32)


def map_features(df: "pd.DataFrame") -> "tuple[dict, pd.DatetimeIndex]":
    features = {}
    times = df.index
    n = len(df)
    def_col = lambda v: np.full(n, v, dtype=np.float32)
    # temp
    if "temp" in df:
        temp = smooth_series(df["temp"].values)
        features["amplitude"] = 0.25 + 0.75 * normalize_series(temp, lo=10, hi=35)
    else:
        logger.warning("缺失 temp 列，使用默认值 0.5")
        features["amplitude"] = def_col(0.5)
    # wind
    if "wind" in df:
        wind = smooth_series(df["wind"].values)
        features["drift"] = 0.10 + 0.90 * normalize_series(wind, lo=0, hi=18)
    else:
        logger.warning("缺失 wind 列，使用默认值 0.5")
        features["drift"] = def_col(0.5)
    # cloud
    if "cloud" in df:
        cloud = smooth_series(df["cloud"].values)
        features["haze"] = 0.30 + 0.70 * normalize_series(cloud, lo=10, hi=100)
    else:
        logger.warning("缺失 cloud 列，使用默认值 0.5")
        features["haze"] = def_col(0.5)
    # hum
    if "hum" in df:
        hum = smooth_series(df["hum"].values)
        features["warmth"] = normalize_series(hum, lo=30, hi=95)
    else:
        logger.warning("缺失 hum 列，使用默认值 0.5")
        features["warmth"] = def_col(0.5)
    for k in features:
        features[k] = features[k].astype(np.float32)
    return features, times
