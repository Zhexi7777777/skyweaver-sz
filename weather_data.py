"""
Weather data fetching and visualization mapping for Shenzhen skyweaver.

This module fetches weather data from Open-Meteo API and maps weather parameters
to visualization parameters for weather art generation.
"""

import pandas as pd
import requests
from datetime import datetime, timedelta
import numpy as np
from scipy import ndimage
from typing import Dict, Tuple


class SkyWeaverWeatherData:
    """
    Handles weather data fetching and parameter mapping for Shenzhen skyweaver visualization.
    """
    
    def __init__(self, latitude: float = 22.5431, longitude: float = 114.0579):
        """
        Initialize with Shenzhen coordinates.
        
        Args:
            latitude: Latitude coordinate (default: Shenzhen)
            longitude: Longitude coordinate (default: Shenzhen)
        """
        self.latitude = latitude
        self.longitude = longitude
        self.base_url = "https://api.open-meteo.com/v1/forecast"
    
    def fetch_weather_data(self) -> pd.DataFrame:
        """
        Fetch hourly weather data for past 5 days plus next 1 day from Open-Meteo.
        
        Returns:
            pandas DataFrame indexed by UTC datetime with columns:
            - temperature (°C)
            - humidity (%)
            - wind_speed (m/s)
            - cloud_cover (%)
        """
        # Calculate date range: past 5 days + next 1 day
        end_date = datetime.now().date() + timedelta(days=1)
        start_date = end_date - timedelta(days=6)
        
        # Prepare API parameters
        params = {
            'latitude': self.latitude,
            'longitude': self.longitude,
            'hourly': 'temperature_2m,relative_humidity_2m,wind_speed_10m,cloud_cover',
            'start_date': start_date.isoformat(),
            'end_date': end_date.isoformat(),
            'timezone': 'UTC'
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            response.raise_for_status()
            data = response.json()
            
            # Extract hourly data
            hourly_data = data['hourly']
            
            # Create DataFrame
            df = pd.DataFrame({
                'temperature': hourly_data['temperature_2m'],
                'humidity': hourly_data['relative_humidity_2m'],
                'wind_speed': hourly_data['wind_speed_10m'],
                'cloud_cover': hourly_data['cloud_cover']
            })
            
            # Set datetime index
            df.index = pd.to_datetime(hourly_data['time'])
            df.index.name = 'datetime_utc'
            
            return df
            
        except requests.RequestException as e:
            raise RuntimeError(f"Failed to fetch weather data: {e}")
        except KeyError as e:
            raise RuntimeError(f"Unexpected API response format: {e}")
    
    def normalize_values(self, series: pd.Series, target_range: Tuple[float, float] = (0, 1)) -> pd.Series:
        """
        Normalize a pandas Series to a target range.
        
        Args:
            series: Input data series
            target_range: Target min and max values (default: 0 to 1)
            
        Returns:
            Normalized series
        """
        min_val, max_val = target_range
        series_min, series_max = series.min(), series.max()
        
        if series_max == series_min:
            return pd.Series([min_val] * len(series), index=series.index)
        
        normalized = (series - series_min) / (series_max - series_min)
        normalized = normalized * (max_val - min_val) + min_val
        
        return normalized
    
    def smooth_time_series(self, series: pd.Series, sigma: float = 1.0) -> pd.Series:
        """
        Apply Gaussian smoothing to a time series.
        
        Args:
            series: Input time series
            sigma: Standard deviation for Gaussian kernel
            
        Returns:
            Smoothed time series
        """
        # Handle NaN values
        valid_mask = ~series.isna()
        if not valid_mask.any():
            return series
        
        # Apply Gaussian filter to valid values
        smoothed_values = ndimage.gaussian_filter1d(
            series.values.astype(float), 
            sigma=sigma, 
            mode='nearest'
        )
        
        return pd.Series(smoothed_values, index=series.index)
    
    def map_weather_to_visualization(self, weather_df: pd.DataFrame) -> pd.DataFrame:
        """
        Map weather parameters to visualization parameters with normalization and smoothing.
        
        Args:
            weather_df: DataFrame with weather data
            
        Returns:
            DataFrame with mapped visualization parameters:
            - terrain_amplitude: from temperature
            - horizontal_drift_speed: from wind_speed
            - gamma_haze: from cloud_cover
            - color_warmth: from humidity
        """
        viz_df = pd.DataFrame(index=weather_df.index)
        
        # Temperature -> Terrain amplitude
        # Higher temperature = higher terrain amplitude
        temp_normalized = self.normalize_values(weather_df['temperature'], (0.2, 1.0))
        viz_df['terrain_amplitude'] = self.smooth_time_series(temp_normalized)
        
        # Wind speed -> Horizontal drift speed
        # Higher wind speed = higher drift speed
        wind_normalized = self.normalize_values(weather_df['wind_speed'], (0.1, 1.0))
        viz_df['horizontal_drift_speed'] = self.smooth_time_series(wind_normalized)
        
        # Cloud cover -> Gamma haze (fog)
        # Higher cloud cover = more haze/fog
        cloud_normalized = self.normalize_values(weather_df['cloud_cover'], (0.0, 1.0))
        viz_df['gamma_haze'] = self.smooth_time_series(cloud_normalized)
        
        # Humidity -> Color warmth
        # Higher humidity = warmer colors
        humidity_normalized = self.normalize_values(weather_df['humidity'], (0.0, 1.0))
        viz_df['color_warmth'] = self.smooth_time_series(humidity_normalized)
        
        return viz_df
    
    def get_weather_visualization_data(self) -> Tuple[pd.DataFrame, pd.DataFrame]:
        """
        Complete workflow: fetch weather data and map to visualization parameters.
        
        Returns:
            Tuple of (weather_dataframe, visualization_dataframe)
        """
        weather_df = self.fetch_weather_data()
        viz_df = self.map_weather_to_visualization(weather_df)
        
        return weather_df, viz_df


def main():
    """
    Example usage of the SkyWeaverWeatherData class.
    """
    # Initialize weather data handler
    skyweaver = SkyWeaverWeatherData()
    
    try:
        # Fetch and process data
        weather_data, viz_data = skyweaver.get_weather_visualization_data()
        
        print("Weather Data Sample:")
        print(weather_data.head())
        print(f"\nWeather Data Shape: {weather_data.shape}")
        print(f"Date Range: {weather_data.index.min()} to {weather_data.index.max()}")
        
        print("\nVisualization Parameters Sample:")
        print(viz_data.head())
        print(f"\nVisualization Data Shape: {viz_data.shape}")
        
        # Display some statistics
        print("\nWeather Data Statistics:")
        print(weather_data.describe())
        
        print("\nVisualization Parameters Statistics:")
        print(viz_data.describe())
        
    except Exception as e:
        print(f"Error: {e}")


if __name__ == "__main__":
    main()