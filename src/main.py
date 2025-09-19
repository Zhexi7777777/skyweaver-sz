import os
import argparse
import logging
from fetch import fetch_weather
from map import map_features
from render import make_animation

def main():
    parser = argparse.ArgumentParser(description="Shenzhen Weather Art Visualization Animation Generator")
    parser.add_argument("--days", type=int, default=5, help="Number of days to fetch (past days + 1 future day, default 5)")
    parser.add_argument("--fps", type=int, default=18, help="Animation frame rate (default 18)")
    parser.add_argument("--palette", type=str, default="dusk", help="Palette name (default dusk)")
    parser.add_argument("--accent", type=float, default=0.2, help="Accent parameter 0~1 (default 0.2)")
    parser.add_argument("--width", type=int, default=320, help="Animation width (default 320)")
    parser.add_argument("--height", type=int, default=120, help="Animation height (default 120)")
    parser.add_argument("--out", type=str, default="out/shenzhen.mp4", help="Output file path (default out/shenzhen.mp4)")
    parser.add_argument("--inbetweens", type=int, default=2, help="Number of inbetween frames (default 2)")
    parser.add_argument("--sigma", type=float, default=1.0, help="Feature smoothing sigma (default 1.0)")
    parser.add_argument("--save", action="store_true", help="Save file mode (default is preview mode)")
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format='[%(asctime)s] %(levelname)s: %(message)s')
    logger = logging.getLogger("main")

    city_name = "Shenzhen"
    lat, lon = 22.5431, 114.0579
    tz = "Asia/Shanghai"
    cache_path = "data/weather_shenzhen.parquet"

    try:
        os.makedirs("data", exist_ok=True)
        os.makedirs("out", exist_ok=True)
        logger.info(f"Fetching weather data (days: {args.days}) ...")
        df = fetch_weather(lat, lon, past_days=args.days, forecast_days=1, cache_path=cache_path)
        logger.info(f"Data rows: {len(df)}, time range: {df.index.min()} ~ {df.index.max()}")
        features, times = map_features(df, sigma=args.sigma)
        if args.save:
            logger.info(f"Save mode: generating animation file {args.out}")
            make_animation(
                features, times, args.out, fps=args.fps,
                size=(args.width, args.height), palette=args.palette, accent=args.accent,
                city_name=city_name, lat=lat, lon=lon, tz=tz, inbetweens=args.inbetweens, preview=False, raw_data=df
            )
        else:
            logger.info("Preview mode: displaying animation directly")
            make_animation(
                features, times, None, fps=args.fps,
                size=(args.width, args.height), palette=args.palette, accent=args.accent,
                city_name=city_name, lat=lat, lon=lon, tz=tz, inbetweens=args.inbetweens, preview=True, raw_data=df
            )
        logger.info("Animation generation completed!")
    except Exception as e:
        logger.error(f"Error occurred: {e}")
        print("[Fatal Error] Generation failed. Please check dependencies, network, and parameter settings. See log for details.")

if __name__ == "__main__":
    main()
