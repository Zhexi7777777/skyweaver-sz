import numpy as np
import logging

logger = logging.getLogger(__name__)

_PRESETS = {
    "dusk": [
        (30, 45, 80),    # 更冷的深蓝
        (60, 70, 120),   # 冷蓝紫
        (180, 80, 100)   # 暖色高光（仅在强度顶部10%出现）
    ],
    "coral": [
        (76, 98, 130),   # 薄雾蓝
        (230, 170, 120), # 浅橘
        (242, 120, 100)  # 珊瑚红
    ],
    "twilight": [
        (40, 120, 140),  # 蓝绿
        (70, 60, 120),   # 靛紫
        (200, 80, 160)   # 洋红
    ],
    "deepsea": [
        (20, 40, 80),    # 深海蓝
        (40, 80, 100),   # 青绿
        (120, 130, 140)  # 海雾灰
    ]
}

def get_palette(name: str = "dusk", n: int = 512, accent: float = 0.0) -> np.ndarray:
    if name not in _PRESETS:
        logger.warning(f"未知 palette: {name}，使用 dusk 作为默认")
        name = "dusk"
    stops = np.array(_PRESETS[name], dtype=np.float32) / 255.0
    # 线性插值
    x = np.linspace(0, 1, n)
    c0, c1, c2 = stops
    lut = np.zeros((n, 3), dtype=np.float32)
    for i in range(3):
        lut[:, i] = np.piecewise(x, [x < 0.5, x >= 0.5], [
            lambda t: (1 - t * 2) * c0[i] + (t * 2) * c1[i],
            lambda t: (1 - (t - 0.5) * 2) * c1[i] + ((t - 0.5) * 2) * c2[i]
        ])
    # accent: 高亮端加暖色和亮度
    accent = np.clip(accent, 0, 1)
    if accent > 0:
        if name == "dusk":
            # dusk专用：暖色仅在上10%强度作为高光，增强红相位
            warm_red = np.array([1.0, 0.4, 0.3], dtype=np.float32)  # 偏红暖色
            # 权重函数：只在top 10%有显著效果
            weights = np.maximum(0, (np.linspace(0, 1, n) - 0.9) * 10) ** 2
            lut += (warm_red - lut) * (weights[:, None] * accent * 0.8)
            # 增强高光亮度
            lut += (1.0 - lut) * (weights[:, None] * accent * 0.6)
        elif name == "deepsea":
            # deepsea保持低饱和度
            cool_highlight = np.array([0.8, 0.9, 1.0], dtype=np.float32)
            weights = np.linspace(0, 1, n) ** 3
            lut += (cool_highlight - lut) * (weights[:, None] * accent * 0.3)
        else:
            # 其他配色方案保持原逻辑
            warm = np.array([1.0, 0.7, 0.5], dtype=np.float32)  # 偏暖色
            weights = np.linspace(0, 1, n) ** 2
            lut += (warm - lut) * (weights[:, None] * accent * 0.5)
            lut += (1.0 - lut) * (weights[:, None] * accent * 0.2)
    lut = np.clip(lut, 0, 1)
    return lut

def apply_palette(img01: np.ndarray, lut: np.ndarray) -> np.ndarray:
    if img01.ndim != 2:
        raise ValueError("img01 必须为二维灰度图像")
    if lut.ndim != 2 or lut.shape[1] != 3:
        raise ValueError("lut 必须为 (n,3) 的数组")
    n = lut.shape[0]
    idx = np.clip((img01 * (n - 1)).astype(int), 0, n - 1)
    rgb = lut[idx]
    return rgb.astype(np.float32)
