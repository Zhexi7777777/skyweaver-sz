#!/usr/bin/env python3
"""
Example usage of SkyWeaver Weather Data for Shenzhen.

This script demonstrates how to fetch weather data and map it to visualization parameters.
"""

import sys
import os
from datetime import datetime

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_data import SkyWeaverWeatherData


def main():
    """
    Example demonstrating the complete SkyWeaver weather data workflow.
    """
    print("=" * 60)
    print("SkyWeaver Weather Data Example - Shenzhen")
    print("=" * 60)
    
    try:
        # Initialize the weather data handler for Shenzhen
        print(f"Initializing SkyWeaver for Shenzhen...")
        print(f"Coordinates: 22.5431°N, 114.0579°E")
        skyweaver = SkyWeaverWeatherData()
        
        # Fetch weather data and generate visualization parameters
        print(f"\nFetching weather data from Open-Meteo API...")
        weather_df, viz_df = skyweaver.get_weather_visualization_data()
        
        # Display basic information
        print(f"\n📊 Data Summary:")
        print(f"   • Weather data points: {len(weather_df)}")
        print(f"   • Time range: {weather_df.index.min()} to {weather_df.index.max()}")
        print(f"   • Data interval: {(weather_df.index[1] - weather_df.index[0]).total_seconds()/3600:.0f} hours")
        
        # Show current weather conditions
        current_time = datetime.now().replace(minute=0, second=0, microsecond=0)
        try:
            # Find the closest time to now
            time_diff = abs(weather_df.index - current_time)
            closest_idx = time_diff.argmin()
            current_weather = weather_df.iloc[closest_idx]
            current_viz = viz_df.iloc[closest_idx]
            
            print(f"\n🌤️ Current Weather Conditions (approximate):")
            print(f"   • Temperature: {current_weather['temperature']:.1f}°C")
            print(f"   • Humidity: {current_weather['humidity']:.1f}%")
            print(f"   • Wind Speed: {current_weather['wind_speed']:.1f} m/s")
            print(f"   • Cloud Cover: {current_weather['cloud_cover']:.1f}%")
            
            print(f"\n🎨 Current Visualization Parameters:")
            print(f"   • Terrain Amplitude: {current_viz['terrain_amplitude']:.3f}")
            print(f"   • Horizontal Drift Speed: {current_viz['horizontal_drift_speed']:.3f}")
            print(f"   • Gamma Haze (Fog): {current_viz['gamma_haze']:.3f}")
            print(f"   • Color Warmth: {current_viz['color_warmth']:.3f}")
            
        except Exception as e:
            print(f"   Could not determine current conditions: {e}")
        
        # Show data statistics
        print(f"\n📈 Weather Data Statistics:")
        weather_stats = weather_df.describe()
        for col in weather_df.columns:
            mean_val = weather_stats.loc['mean', col]
            min_val = weather_stats.loc['min', col]
            max_val = weather_stats.loc['max', col]
            unit = {'temperature': '°C', 'humidity': '%', 'wind_speed': ' m/s', 'cloud_cover': '%'}[col]
            print(f"   • {col.replace('_', ' ').title()}: {mean_val:.1f}{unit} (range: {min_val:.1f}-{max_val:.1f}{unit})")
        
        print(f"\n🎯 Visualization Parameter Ranges:")
        viz_stats = viz_df.describe()
        for col in viz_df.columns:
            mean_val = viz_stats.loc['mean', col]
            min_val = viz_stats.loc['min', col]
            max_val = viz_stats.loc['max', col]
            print(f"   • {col.replace('_', ' ').title()}: {mean_val:.3f} (range: {min_val:.3f}-{max_val:.3f})")
        
        # Show sample data
        print(f"\n📋 Sample Data (first 5 hours):")
        print("\nWeather Data:")
        print(weather_df.head().round(2).to_string())
        
        print("\nVisualization Parameters:")
        print(viz_df.head().round(3).to_string())
        
        # Parameter relationships
        print(f"\n🔗 Parameter Correlations:")
        correlations = [
            ('Temperature', 'Terrain Amplitude', weather_df['temperature'].corr(viz_df['terrain_amplitude'])),
            ('Wind Speed', 'Horizontal Drift', weather_df['wind_speed'].corr(viz_df['horizontal_drift_speed'])),
            ('Cloud Cover', 'Gamma Haze', weather_df['cloud_cover'].corr(viz_df['gamma_haze'])),
            ('Humidity', 'Color Warmth', weather_df['humidity'].corr(viz_df['color_warmth']))
        ]
        
        for weather_param, viz_param, corr in correlations:
            print(f"   • {weather_param} → {viz_param}: {corr:.3f}")
        
        print(f"\n✅ Success! Weather data fetched and mapped to visualization parameters.")
        print(f"💡 Use these DataFrames for your weather art visualization:")
        print(f"   • weather_df: Raw weather data")
        print(f"   • viz_df: Normalized visualization parameters")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        print(f"\n💡 If you see a network error, this might be due to:")
        print(f"   • No internet connection")
        print(f"   • Open-Meteo API temporarily unavailable")
        print(f"   • Firewall blocking the request")
        print(f"\n🧪 To test functionality with mock data, run:")
        print(f"   python test_weather_mock.py")
        sys.exit(1)


if __name__ == "__main__":
    main()