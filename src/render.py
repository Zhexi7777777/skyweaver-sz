import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
import matplotlib.patheffects as path_effects
from matplotlib import cm
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from datetime import datetime
from pytz import timezone, UTC
from palettes import get_palette, apply_palette

# 配置 matplotlib 字体以避免锯齿
plt.rcParams['font.family'] = ['DejaVu Sans', 'Arial', 'sans-serif']
plt.rcParams['axes.unicode_minus'] = False

try:
    import noise  # type: ignore
    _HAS_NOISE = True
except ImportError:
    noise = None  # type: ignore
    _HAS_NOISE = False
    from scipy.ndimage import gaussian_filter

logger = logging.getLogger(__name__)


def _gen_noise_field(shape, seed=0, octaves=4, persistence=0.55, lacunarity=2.0):
    h, w = shape
    if _HAS_NOISE and noise is not None:
        arr = np.zeros((h, w), dtype=np.float32)
        scale = 0.08
        for y in range(h):
            for x in range(w):
                arr[y, x] = noise.pnoise2(
                    x * scale, y * scale,
                    octaves=octaves, persistence=persistence, lacunarity=lacunarity,
                    repeatx=w, repeaty=h, base=seed
                )
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    else:
        np.random.seed(seed)
        arr = np.random.rand(h, w).astype(np.float32)
        arr = gaussian_filter(arr, sigma=6)
        arr = (arr - arr.min()) / (arr.max() - arr.min() + 1e-8)
    return arr


def _blend_palette(lut1, lut2, alpha):
    return lut1 * (1 - alpha) + lut2 * alpha


def make_animation(features: dict, times: "pd.DatetimeIndex", out_path: str = None, fps: int = 18, size: "tuple[int,int]" = (320, 120), palette: str = "dusk", accent: float = 0.15, city_name: str = "Shenzhen", lat: float = 22.5431, lon: float = 114.0579, tz: str = "Asia/Shanghai", inbetweens: int = 0, preview: bool = False, raw_data: "pd.DataFrame" = None) -> None:
    if out_path and not preview:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    h, w = size[1], size[0]
    n_frames = len(times) * (inbetweens + 1)
    logger.info(f"生成动画帧数: {n_frames}")
    # 预生成噪声基底
    base_noise = _gen_noise_field((h, w), seed=42)
    ridge_noise = _gen_noise_field((h, w), seed=99)
    lut1 = get_palette(palette, n=512, accent=accent)
    lut2 = get_palette("coral", n=512, accent=accent)
    frames = []
    for i in range(len(times)):
        for k in range(inbetweens + 1):
            # 计算当前时间索引（对于插值帧，时间保持在基准时间点）
            t_idx = i
            alpha = k / (inbetweens + 1) if inbetweens > 0 else 0
            # 插值特征
            def interp(key):
                arr = features[key]
                if t_idx < len(arr) - 1:
                    return arr[t_idx] * (1 - alpha) + arr[t_idx + 1] * alpha
                else:
                    return arr[t_idx]
            amplitude = interp("amplitude")
            drift = interp("drift")
            haze = interp("haze")
            warmth = interp("warmth")
            # 地形生成
            offset = int(drift * (i * (inbetweens + 1) + k) * 2) % w
            terrain = np.roll(base_noise, offset, axis=1)
            ridge = np.roll(ridge_noise, offset // 2, axis=1)
            img = amplitude * terrain + (1 - amplitude) * ridge
            img = (img - img.min()) / (img.max() - img.min() + 1e-8)
            # gamma 雾化
            gamma = 0.8 + haze * 0.9
            img = np.power(img, gamma)
            # LUT 混合
            lut = _blend_palette(lut1, lut2, warmth)
            rgb = apply_palette(img, lut)
            # 文字叠加
            fig, ax = plt.subplots(figsize=(w/80, h/80), dpi=80)
            ax.imshow(rgb, interpolation="bilinear")
            ax.axis("off")
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
            
            # 底部半透明黑条背景（增强对比度和高度）
            bottom_bar_height = 22
            ax.add_patch(plt.Rectangle((0, h-bottom_bar_height), w, bottom_bar_height, 
                                     facecolor='black', alpha=0.75, zorder=10))
            
            # 获取时间和数值
            utc_dt = times[t_idx].to_pydatetime().replace(tzinfo=UTC)
            try:
                local_dt = utc_dt.astimezone(timezone(tz))
            except Exception:
                local_dt = utc_dt
            
            tval = interp("amplitude")
            hval = interp("warmth") 
            wval = interp("drift")
            cval = interp("haze")
            
            # 获取真实天气数据用于显示
            if raw_data is not None and t_idx < len(raw_data):
                # 显示真实的天气数据值
                real_temp = raw_data.iloc[t_idx]['temp'] if 'temp' in raw_data.columns else 0
                real_hum = raw_data.iloc[t_idx]['hum'] if 'hum' in raw_data.columns else 0
                real_wind = raw_data.iloc[t_idx]['wind'] if 'wind' in raw_data.columns else 0
                real_cloud = raw_data.iloc[t_idx]['cloud'] if 'cloud' in raw_data.columns else 0
            else:
                # 回退到特征值
                real_temp = tval * 35  # 近似反推温度
                real_hum = hval * 100  # 近似反推湿度
                real_wind = wval * 18  # 近似反推风速
                real_cloud = cval * 100  # 近似反推云量
            
            # 优化文字布局，避免重叠 - 使用两行布局
            
            # 第一行：城市和时间
            top_y = h - 18
            # 左侧：城市
            city_display = "Shenzhen" if city_name in ["深圳", "Shenzhen"] else city_name
            ax.text(6, top_y, f"{city_display} ({lat:.1f},{lon:.1f})", 
                   color="#ffffff", fontsize=8, va="center", ha="left", weight="bold", 
                   alpha=1.0, zorder=12, family='sans-serif',
                   path_effects=[path_effects.withStroke(linewidth=2, foreground='#000000')])
            
            # 右侧：时间
            time_text = f"{local_dt.strftime('%m-%d %H:%M')} | {utc_dt.strftime('%H:%M')} UTC"
            ax.text(w-6, top_y, time_text,
                   color="#ffffff", fontsize=8, va="center", ha="right", weight="bold",
                   alpha=1.0, zorder=12, family='sans-serif',
                   path_effects=[path_effects.withStroke(linewidth=2, foreground='#000000')])
            
            # 第二行：天气数据（居中显示）
            bottom_y = h - 6
            data_text = f"T:{real_temp:.1f}°C  H:{real_hum:.0f}%  W:{real_wind:.1f}m/s  C:{real_cloud:.0f}%"
            ax.text(w//2, bottom_y, data_text,
                   color="#ffffff", fontsize=8, va="center", ha="center", weight="bold",
                   alpha=1.0, zorder=12, family='sans-serif',
                   path_effects=[path_effects.withStroke(linewidth=2, foreground='#000000')])
            fig.canvas.draw()
            frame = np.frombuffer(fig.canvas.buffer_rgba(), dtype=np.uint8)
            frame = frame.reshape(fig.canvas.get_width_height()[::-1] + (4,))[:, :, :3]
            frames.append(frame)
            plt.close(fig)
    
    # 预览模式：直接显示动画
    if preview:
        logger.info("启动动画预览窗口...")
        fig, ax = plt.subplots(figsize=(w/80, h/80), dpi=80)
        im = ax.imshow(frames[0], interpolation="bilinear")
        ax.axis("off")
        preview_title = "Shenzhen Weather Daily"
        ax.set_title(preview_title, fontsize=12, color="white", weight="bold")
        fig.patch.set_facecolor('black')
        
        def update(i):
            im.set_data(frames[i])
            return [im]
        
        anim = FuncAnimation(fig, update, frames=len(frames), interval=1000//fps, blit=True, repeat=True)
        plt.show()
        logger.info("预览完成！")
        return
    
    # 文件保存模式
    if not out_path:
        logger.error("非预览模式需要指定输出路径")
        return
        
    # 导出
    try:
        logger.info(f"尝试保存 mp4: {out_path}")
        writer = FFMpegWriter(fps=fps, metadata={"title": city_name})
        fig, ax = plt.subplots(figsize=(w/80, h/80), dpi=80)
        im = ax.imshow(frames[0], interpolation="bilinear")
        ax.axis("off")
        def update(i):
            im.set_data(frames[i])
            return [im]
        anim = FuncAnimation(fig, update, frames=len(frames), blit=True)
        anim.save(out_path, writer=writer, dpi=80, savefig_kwargs={"pad_inches":0, "bbox_inches":'tight'})
        plt.close(fig)
        logger.info(f"动画已保存为 mp4: {out_path}")
    except Exception as e:
        logger.warning(f"mp4 保存失败: {e}，尝试保存 GIF")
        gif_path = os.path.splitext(out_path)[0] + ".gif"
        try:
            writer = PillowWriter(fps=fps)
            fig, ax = plt.subplots(figsize=(w/80, h/80), dpi=80)
            im = ax.imshow(frames[0], interpolation="bilinear")
            ax.axis("off")
            def update(i):
                im.set_data(frames[i])
                return [im]
            anim = FuncAnimation(fig, update, frames=len(frames), blit=True)
            anim.save(gif_path, writer=writer, dpi=80, savefig_kwargs={"pad_inches":0, "bbox_inches":'tight'})
            plt.close(fig)
            logger.info(f"动画已保存为 GIF: {gif_path}")
        except Exception as e2:
            logger.error(f"GIF 保存也失败: {e2}")
            raise
