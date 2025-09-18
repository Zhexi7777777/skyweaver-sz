import os
import logging
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt
from matplotlib import cm
from matplotlib.animation import FuncAnimation, FFMpegWriter, PillowWriter
from datetime import datetime
from pytz import timezone, UTC
from palettes import get_palette, apply_palette

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


def make_animation(features: dict, times: "pd.DatetimeIndex", out_path: str = None, fps: int = 12, size: "tuple[int,int]" = (320, 120), palette: str = "dusk", accent: float = 0.15, city_name: str = "Shenzhen", lat: float = 22.5431, lon: float = 114.0579, tz: str = "Asia/Shanghai", inbetweens: int = 0, preview: bool = False) -> None:
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
            # 顶部左侧
            ax.text(6, 12, f"{city_name}  ({lat:.4f}, {lon:.4f})", color="#fff", fontsize=10, va="top", ha="left", weight="bold", alpha=0.92, backgroundcolor=(0,0,0,0.18))
            # 下方本地/UTC时间
            utc_dt = times[t_idx].to_pydatetime().replace(tzinfo=UTC)
            try:
                local_dt = utc_dt.astimezone(timezone(tz))
            except Exception:
                local_dt = utc_dt
            ax.text(6, h-8, f"{local_dt.strftime('%Y-%m-%d %H:%M')} {tz} / {utc_dt.strftime('%H:%M')} UTC", color="#fff", fontsize=9, va="bottom", ha="left", alpha=0.88, backgroundcolor=(0,0,0,0.15))
            # 右下角数值
            tval = interp("amplitude")
            hval = interp("warmth")
            wval = interp("drift")
            cval = interp("haze")
            ax.text(w-8, h-8, f"T:{tval:.2f} RH:{hval:.2f} W:{wval:.2f} C:{cval:.2f}", color="#fff", fontsize=9, va="bottom", ha="right", alpha=0.88, backgroundcolor=(0,0,0,0.15))
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
        ax.set_title(f"{city_name} 天气艺术可视化 (按 Q 键退出)", fontsize=12, color="white", weight="bold")
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
