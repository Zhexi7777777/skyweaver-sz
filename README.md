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

### 最简单运行方式（默认预览模式）
```bash
# 使用批处理脚本（推荐）
run.bat

# 或直接运行 Python
python src/main.py
```

### 快速预览不同效果
```bash
run.bat --palette coral           # 珊瑚色调
run.bat --palette twilight        # 暮光色调  
run.bat --palette deepsea          # 深海蓝绿（新增）
run.bat --accent 0.5              # 更强高光效果
run.bat --palette dusk --accent 0.8 # 冷蓝紫主调+强红色高光
```

### 保存文件模式
```bash
run.bat --save --out my_weather.mp4    # 保存为 mp4
run.bat --save --days 7                # 保存 7 天数据
```

### 参数说明
- `--save`      启用保存模式（默认为预览模式）
- `--days`      获取过去几天+未来一天数据（默认3）
- `--fps`       动画帧率（默认18，更流畅）
- `--palette`   调色板主题（dusk=冷蓝紫/coral=暖橘/twilight=洋红/deepsea=深海蓝绿）
- `--accent`    高光参数 0~1（默认0.2，增强时提升亮度和红相位）
- `--width`     输出宽度（默认320）
- `--height`    输出高度（默认120）
- `--out`       输出文件路径（仅保存模式需要）
- `--inbetweens` 相邻小时间插值帧数（平滑动画，默认0）

### 界面说明
- **底部信息栏**：增强对比度的半透明黑色背景条，双行布局避免重叠
  - 第一行：左侧城市坐标，右侧本地时间和UTC时间
  - 第二行：居中显示完整天气数据（温度/湿度/风速/云量）
- **预览标题**：Shenzhen Weather Daily
- **高清显示**：8px字体配合2px黑色描边，确保清晰可读
- **抗锯齿显示**：优化字体渲染，确保GIF保存时文字清晰无锯齿

### 配色方案详解
- **dusk**：冷蓝紫主调，暖色仅在上10%强度作为高光，accent增强时偏红
- **coral**：薄雾蓝到暖橘珊瑚，温暖明亮
- **twilight**：蓝绿到靛紫到洋红，神秘暮色
- **deepsea**：深海蓝到青绿到海雾灰，整体低饱和度
- `--out`       输出文件路径（仅保存模式需要）
- `--inbetweens` 相邻小时间插值帧数（平滑动画，默认0）

### 使用建议
- **最快体验**：直接运行 `run.bat` 查看效果
- **调试参数**：`run.bat --palette coral --accent 0.3` 等
- **最终输出**：`run.bat --save --out final.mp4` 生成文件

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
