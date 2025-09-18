import os
import argparse
import logging
from fetch import fetch_weather
from map import map_features
from render import make_animation

def main():
    parser = argparse.ArgumentParser(description="深圳天气艺术可视化动画生成器")
    parser.add_argument("--days", type=int, default=3, help="获取过去几天+未来一天的数据 (默认3)")
    parser.add_argument("--fps", type=int, default=12, help="动画帧率 (默认12)")
    parser.add_argument("--palette", type=str, default="dusk", help="调色板名称 (默认dusk)")
    parser.add_argument("--accent", type=float, default=0.2, help="高光参数 0~1 (默认0.2)")
    parser.add_argument("--width", type=int, default=320, help="动画宽度 (默认320)")
    parser.add_argument("--height", type=int, default=120, help="动画高度 (默认120)")
    parser.add_argument("--out", type=str, default="out/shenzhen.mp4", help="输出文件路径 (默认out/shenzhen.mp4)")
    parser.add_argument("--inbetweens", type=int, default=0, help="插值帧数 (默认0)")
    parser.add_argument("--save", action="store_true", help="保存文件模式（默认为预览模式）")
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
        logger.info(f"获取天气数据（天数: {args.days}）...")
        df = fetch_weather(lat, lon, past_days=args.days, forecast_days=1, cache_path=cache_path)
        logger.info(f"数据行数: {len(df)}，时间范围: {df.index.min()} ~ {df.index.max()}")
        features, times = map_features(df)
        if args.save:
            logger.info(f"保存模式：生成动画文件 {args.out}")
            make_animation(
                features, times, args.out, fps=args.fps,
                size=(args.width, args.height), palette=args.palette, accent=args.accent,
                city_name=city_name, lat=lat, lon=lon, tz=tz, inbetweens=args.inbetweens, preview=False
            )
        else:
            logger.info("预览模式：直接显示动画")
            make_animation(
                features, times, None, fps=args.fps,
                size=(args.width, args.height), palette=args.palette, accent=args.accent,
                city_name=city_name, lat=lat, lon=lon, tz=tz, inbetweens=args.inbetweens, preview=True
            )
        logger.info("动画生成完成！")
    except Exception as e:
        logger.error(f"发生错误: {e}")
        print("[致命错误] 生成失败，请检查依赖、网络和参数设置。详细信息见日志。")

if __name__ == "__main__":
    main()
