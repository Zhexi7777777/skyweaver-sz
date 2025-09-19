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
from scipy.ndimage import gaussian_filter, map_coordinates

 # Configure matplotlib font to avoid aliasing
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


def _gen_noise_field_vectorized(shape, steps=64, seed=0, octaves=4, persistence=0.55, lacunarity=2.0):
    h, w = shape
    scale = 0.08
    np.random.seed(seed)
    if _HAS_NOISE and noise is not None:
        xs = np.arange(w)
        ys = np.arange(h)
        X, Y = np.meshgrid(xs, ys)
        arrs = np.zeros((steps, h, w), dtype=np.float32)
        for t in range(steps):
            phase = t / steps * 8.0  # 8.0: Controls the period length
            arrs[t] = np.vectorize(lambda x, y: noise.pnoise2(
                (x * scale) + phase, (y * scale) + phase,
                octaves=octaves, persistence=persistence, lacunarity=lacunarity,
                repeatx=w, repeaty=h, base=seed
            ))(X, Y)
        arrs = (arrs - arrs.min()) / (arrs.max() - arrs.min() + 1e-8)
    else:
        arrs = np.random.rand(steps, h, w).astype(np.float32)
        for t in range(steps):
            arrs[t] = gaussian_filter(arrs[t], sigma=6)
        arrs = (arrs - arrs.min()) / (arrs.max() - arrs.min() + 1e-8)
    return arrs


def _blend_palette(lut1, lut2, alpha):
    return lut1 * (1 - alpha) + lut2 * alpha


def make_animation(features: dict, times: "pd.DatetimeIndex", out_path: str = None, fps: int = 18, size: "tuple[int,int]" = (320, 120), palette: str = "dusk", accent: float = 0.15, city_name: str = "Shenzhen", lat: float = 22.5431, lon: float = 114.0579, tz: str = "Asia/Shanghai", inbetweens: int = 0, preview: bool = False, raw_data: "pd.DataFrame" = None, noise_steps: int = 64) -> None:
    if out_path and not preview:
        os.makedirs(os.path.dirname(out_path), exist_ok=True)
    h, w = size[1], size[0]
    n_frames = len(times) * (inbetweens + 1)
    logger.info(f"Number of animation frames: {n_frames}")
    # Pre-generate multi-layer noise slices
    base_noise_arr = _gen_noise_field_vectorized((h, w), steps=noise_steps, seed=42)
    ridge_noise_arr = _gen_noise_field_vectorized((h, w), steps=noise_steps, seed=99)
    cloud_noise_arr = _gen_noise_field_vectorized((h, w), steps=noise_steps, seed=123, octaves=2, persistence=0.7)
    ripple_noise_arr = _gen_noise_field_vectorized((h, w), steps=noise_steps, seed=321, octaves=6, persistence=0.3)
    flow_noise_arr = _gen_noise_field_vectorized((h, w), steps=noise_steps, seed=888, octaves=3, persistence=0.5)
    # Adjustable weights
    WEIGHTS = dict(terrain=0.5, ridge=0.18, cloud=0.18, ripple=0.08, flow=0.06)
    BLUR_SIGMA = 1.0  # Blur radius
    DISTORT_STRENGTH = 6.0  # Dynamic distortion strength (pixels)
    DISTORT_FREQ = 1.0  # Distortion frequency
    lut1 = get_palette(palette, n=512, accent=accent)
    lut2 = get_palette("coral", n=512, accent=accent)
    frames = []
    for i in range(len(times)):
        for k in range(inbetweens + 1):
            alpha = k / (inbetweens + 1) if inbetweens > 0 else 0
            def interp(key):
                arr = features[key]
                if i < len(arr) - 1:
                    return arr[i] * (1 - alpha) + arr[i + 1] * alpha
                else:
                    return arr[i]
            amplitude = interp("amplitude")
            drift = interp("drift")
            haze = interp("haze")
            warmth = interp("warmth")
            global_idx = i * (inbetweens + 1) + k
            drift0 = features["drift"][i]
            drift1 = features["drift"][i+1] if i < len(times)-1 else features["drift"][i]
            drift_interp = drift0 * (1 - alpha) + drift1 * alpha
            phase = (drift_interp * global_idx * 2) % noise_steps
            idx0 = int(np.floor(phase))
            idx1 = (idx0 + 1) % noise_steps
            frac = phase - idx0
            terrain = base_noise_arr[idx0] * (1 - frac) + base_noise_arr[idx1] * frac
            ridge = ridge_noise_arr[idx0] * (1 - frac) + ridge_noise_arr[idx1] * frac
            cloud = cloud_noise_arr[idx0] * (1 - frac) + cloud_noise_arr[idx1] * frac
            ripple = ripple_noise_arr[idx0] * (1 - frac) + ripple_noise_arr[idx1] * frac
            flow = flow_noise_arr[idx0] * (1 - frac) + flow_noise_arr[idx1] * frac
            # Multi-layer noise blending
            img = (
                WEIGHTS['terrain'] * terrain +
                WEIGHTS['ridge'] * ridge +
                WEIGHTS['cloud'] * cloud +
                WEIGHTS['ripple'] * ripple +
                WEIGHTS['flow'] * flow
            )
            img = (img - img.min()) / (img.max() - img.min() + 1e-8)
            # Dynamic distortion
            t = global_idx / n_frames * DISTORT_FREQ * 2 * np.pi
            dx = DISTORT_STRENGTH * np.sin(flow * 2 * np.pi + t)
            dy = DISTORT_STRENGTH * np.cos(cloud * 2 * np.pi + t)
            coords_x, coords_y = np.meshgrid(np.arange(w), np.arange(h))
            coords = np.array([coords_y + dy, coords_x + dx])
            img = map_coordinates(img, coords, order=1, mode='reflect')
            # Smoothing
            img = gaussian_filter(img, sigma=BLUR_SIGMA)
            gamma = 0.8 + haze * 0.9
            img = np.power(img, gamma)
            lut = _blend_palette(lut1, lut2, warmth)
            rgb = apply_palette(img, lut)
            # Text overlay
            fig, ax = plt.subplots(figsize=(w/80, h/80), dpi=80)
            ax.imshow(rgb, interpolation="bilinear")
            ax.axis("off")
            plt.subplots_adjust(left=0, right=1, top=1, bottom=0, wspace=0, hspace=0)
            # Bottom semi-transparent black bar background (enhances contrast and height)
            bottom_bar_height = 22
            ax.add_patch(plt.Rectangle((0, h-bottom_bar_height), w, bottom_bar_height, 
                                     facecolor='black', alpha=0.75, zorder=10))
            # Get time and values
            t_idx = i
            utc_dt = times[t_idx].to_pydatetime().replace(tzinfo=UTC)
            try:
                local_dt = utc_dt.astimezone(timezone(tz))
            except Exception:
                local_dt = utc_dt
            tval = interp("amplitude")
            hval = interp("warmth") 
            wval = interp("drift")
            cval = interp("haze")
            # Get real weather data for display
            if raw_data is not None and t_idx < len(raw_data):
                # Display real weather data values
                real_temp = raw_data.iloc[t_idx]['temp'] if 'temp' in raw_data.columns else 0
                real_hum = raw_data.iloc[t_idx]['hum'] if 'hum' in raw_data.columns else 0
                real_wind = raw_data.iloc[t_idx]['wind'] if 'wind' in raw_data.columns else 0
                real_cloud = raw_data.iloc[t_idx]['cloud'] if 'cloud' in raw_data.columns else 0
            else:
                # Fallback to feature values
                real_temp = tval * 35  # Approximate temperature
                real_hum = hval * 100  # Approximate humidity
                real_wind = wval * 18  # Approximate wind speed
                real_cloud = cval * 100  # Approximate cloud cover
            
            # Optimize text layout, avoid overlap - use two-line layout
            
            # First line: city and time
            top_y = h - 18
            # Left: city
            city_display = "Shenzhen" if city_name in ["深圳", "Shenzhen"] else city_name
            ax.text(6, top_y, f"{city_display} ({lat:.1f},{lon:.1f})", 
                   color="#ffffff", fontsize=8, va="center", ha="left", weight="bold", 
                   alpha=1.0, zorder=12, family='sans-serif',
                   path_effects=[path_effects.withStroke(linewidth=2, foreground='#000000')])
            
            # Right: time
            time_text = f"{local_dt.strftime('%m-%d %H:%M')} | {utc_dt.strftime('%H:%M')} UTC"
            ax.text(w-6, top_y, time_text,
                   color="#ffffff", fontsize=8, va="center", ha="right", weight="bold",
                   alpha=1.0, zorder=12, family='sans-serif',
                   path_effects=[path_effects.withStroke(linewidth=2, foreground='#000000')])
            
            # Second line: weather data (centered)
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
    
    # Preview mode: directly display animation
    if preview:
        logger.info("Launching animation preview window...")
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
        logger.info("Preview finished!")
        return
    
    # File save mode
    if not out_path:
        logger.error("Output path must be specified in non-preview mode")
        return
    # Export
    try:
        logger.info(f"Attempting to save mp4: {out_path}")
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
        logger.info(f"Animation saved as mp4: {out_path}")
    except Exception as e:
        logger.warning(f"mp4 save failed: {e}, trying GIF")
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
            logger.info(f"Animation saved as GIF: {gif_path}")
        except Exception as e2:
            logger.error(f"GIF save also failed: {e2}")
            raise
