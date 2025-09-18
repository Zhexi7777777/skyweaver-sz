# skyweaver-sz
The weather art visualization in Shenzhen.
## 深圳天气艺术可视化

> 用天气数据驱动的地形动画，艺术化展现深圳的气象呼吸。

---

![效果截图占位](docs/screenshot_placeholder.png)

---

## 数据源说明
- **来源**：[Open-Meteo](https://open-meteo.com/)
- **API**：`https://api.open-meteo.com/v1/forecast`
- **请求参数**：`latitude, longitude, past_days, forecast_days, hourly=temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover, timezone=UTC`
- **许可证**：免费公开，详见 [Open-Meteo License](https://open-meteo.com/en/docs#license)

---

## 安装步骤
```bash
# 1. 创建虚拟环境（推荐）
python -m venv .venv
.venv\Scripts\activate  # Windows
# 或 source .venv/bin/activate  # macOS/Linux

# 2. 安装依赖
pip install -r requirements.txt

# 3. 安装 ffmpeg（建议用于 mp4 导出）
# Windows: 可用 choco install ffmpeg 或下载 release
# macOS:   brew install ffmpeg
# Linux:   sudo apt install ffmpeg
```

---

## 运行示例与参数说明
```bash
python src/main.py --days 5 --fps 12 --palette dusk --accent 0.15 --width 320 --height 120 --out out/shenzhen.mp4 --inbetweens 2
```
- `--days`      获取过去几天+未来一天数据（默认5）
- `--fps`       动画帧率（默认12）
- `--palette`   调色板主题（dusk/coral/twilight）
- `--accent`    高光参数 0~1（默认0.15，越大越暖亮）
- `--width`     输出宽度（默认320）
- `--height`    输出高度（默认120）
- `--out`       输出文件路径
- `--inbetweens` 相邻小时间插值帧数（平滑动画，默认0）

---

## 数据与视觉映射
- **温度** → 地形振幅（起伏幅度）
- **风速** → 地形漂移速度（水平流动）
- **云量** → 雾化强度（gamma 雾化）
- **湿度** → 色温（冷暖色调）

---

## 缓存策略与时区说明
- 天气数据缓存于 `data/weather_shenzhen.parquet`，每小时自动刷新，网络失败时自动回退旧缓存。
- 数据索引为 UTC，动画标题自动标注本地时区（Asia/Shanghai）与 UTC 时间。

---

## 常见问题与解决
- **ffmpeg 缺失**：无法导出 mp4，自动回退为 GIF。请优先安装 ffmpeg 以获得更高质量动画。
- **网络失败**：如遇 API 请求失败，将自动使用本地缓存数据（如有）。
- **依赖缺失**：请确保 requirements.txt 全部安装，pyarrow 或 fastparquet 至少有一个。

---

## 许可证与致谢
- 本项目采用 MIT License。
- 天气数据由 [Open-Meteo](https://open-meteo.com/) 免费提供，致谢其开放 API。
