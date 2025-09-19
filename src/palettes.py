import numpy as np
import logging

logger = logging.getLogger(__name__)

_PRESETS = {
    "dusk": [
        (30, 45, 80),    # Colder deep blue
        (60, 70, 120),   # Cool blue-violet
        (180, 80, 100)   # Warm highlight (only appears at top 10% intensity)
    ],
    "coral": [
        (76, 98, 130),   # Mist blue
        (230, 170, 120), # Light orange
        (242, 120, 100)  # Coral red
    ],
    "twilight": [
        (40, 120, 140),  # Blue-green
        (70, 60, 120),   # Violet
        (200, 80, 160)   # Magenta
    ],
    "deepsea": [
        (20, 40, 80),    # Deep sea blue
        (40, 80, 100),   # Cyan-green
        (120, 130, 140)  # Sea mist gray
    ]
}

def get_palette(name: str = "dusk", n: int = 512, accent: float = 0.0) -> np.ndarray:
    if name not in _PRESETS:
        logger.warning(f"Unknown palette: {name}, using dusk as default")
        name = "dusk"
    stops = np.array(_PRESETS[name], dtype=np.float32) / 255.0
    # Linear interpolation
    x = np.linspace(0, 1, n)
    c0, c1, c2 = stops
    lut = np.zeros((n, 3), dtype=np.float32)
    for i in range(3):
        lut[:, i] = np.piecewise(x, [x < 0.5, x >= 0.5], [
            lambda t: (1 - t * 2) * c0[i] + (t * 2) * c1[i],
            lambda t: (1 - (t - 0.5) * 2) * c1[i] + ((t - 0.5) * 2) * c2[i]
        ])
    # accent: Add warm color and brightness to highlight end
    accent = np.clip(accent, 0, 1)
    if accent > 0:
        if name == "dusk":
            # dusk only: warm color only as highlight in top 10% intensity, enhance red phase
            warm_red = np.array([1.0, 0.4, 0.3], dtype=np.float32)  # Warm reddish color
            # Weight function: only significant effect in top 10%
            weights = np.maximum(0, (np.linspace(0, 1, n) - 0.9) * 10) ** 2
            lut += (warm_red - lut) * (weights[:, None] * accent * 0.8)
            # Enhance highlight brightness
            lut += (1.0 - lut) * (weights[:, None] * accent * 0.6)
        elif name == "deepsea":
            # deepsea keeps low saturation
            cool_highlight = np.array([0.8, 0.9, 1.0], dtype=np.float32)
            weights = np.linspace(0, 1, n) ** 3
            lut += (cool_highlight - lut) * (weights[:, None] * accent * 0.3)
        else:
            # Other palettes keep original logic
            warm = np.array([1.0, 0.7, 0.5], dtype=np.float32)  # Warm color
            weights = np.linspace(0, 1, n) ** 2
            lut += (warm - lut) * (weights[:, None] * accent * 0.5)
            lut += (1.0 - lut) * (weights[:, None] * accent * 0.2)
    lut = np.clip(lut, 0, 1)
    return lut

def apply_palette(img01: np.ndarray, lut: np.ndarray) -> np.ndarray:
    if img01.ndim != 2:
        raise ValueError("img01 must be a 2D grayscale image")
    if lut.ndim != 2 or lut.shape[1] != 3:
        raise ValueError("lut must be an array of shape (n,3)")
    n = lut.shape[0]
    idx = np.clip((img01 * (n - 1)).astype(int), 0, n - 1)
    rgb = lut[idx]
    return rgb.astype(np.float32)
