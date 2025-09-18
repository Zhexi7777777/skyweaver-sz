# skyweaver-sz
The weather art visualization in Shenzhen.

## Overview

This project fetches real-time weather data for Shenzhen and maps it to visualization parameters for weather art generation. It uses the Open-Meteo API to get hourly weather data and transforms it into parameters suitable for visual art rendering.

## Features

- **Weather Data Fetching**: Retrieves hourly temperature, humidity, wind speed, and cloud cover data for the past 5 days plus next 1 day from Open-Meteo API
- **Data Processing**: Returns data as a pandas DataFrame indexed by UTC datetime
- **Visualization Mapping**: Maps weather parameters to visual elements:
  - Temperature → Terrain amplitude (higher temperature = higher terrain)
  - Wind speed → Horizontal drift speed (higher wind = more movement)
  - Cloud cover → Gamma haze/fog (more clouds = more haze)
  - Humidity → Color warmth (higher humidity = warmer colors)
- **Data Enhancement**: Includes normalization and time-based smoothing for better visual transitions

## Installation

```bash
pip install -r requirements.txt
```

## Usage

### Basic Usage

```python
from weather_data import SkyWeaverWeatherData

# Initialize for Shenzhen (default coordinates)
skyweaver = SkyWeaverWeatherData()

# Fetch weather data and get visualization parameters
weather_df, viz_df = skyweaver.get_weather_visualization_data()

print("Weather data shape:", weather_df.shape)
print("Visualization parameters shape:", viz_df.shape)
print("\nSample visualization parameters:")
print(viz_df.head())
```

### Custom Location

```python
# Use custom coordinates
skyweaver = SkyWeaverWeatherData(latitude=22.5431, longitude=114.0579)
weather_df = skyweaver.fetch_weather_data()
```

### Individual Components

```python
# Just fetch weather data
weather_df = skyweaver.fetch_weather_data()

# Map to visualization parameters
viz_df = skyweaver.map_weather_to_visualization(weather_df)
```

## Data Structure

### Weather Data DataFrame
- **Index**: UTC datetime (hourly intervals)
- **Columns**: 
  - `temperature`: Temperature in °C
  - `humidity`: Relative humidity in %
  - `wind_speed`: Wind speed at 10m in m/s
  - `cloud_cover`: Cloud cover in %

### Visualization Parameters DataFrame
- **Index**: UTC datetime (same as weather data)
- **Columns**:
  - `terrain_amplitude`: Normalized value [0.2, 1.0] for terrain height variation
  - `horizontal_drift_speed`: Normalized value [0.1, 1.0] for movement speed
  - `gamma_haze`: Normalized value [0.0, 1.0] for fog/haze intensity
  - `color_warmth`: Normalized value [0.0, 1.0] for color temperature

## Testing

Run the test suite to validate functionality:

```bash
# Test with mock data (no internet required)
python test_weather_mock.py

# Test with real API data (requires internet)
python test_weather.py

# Run the main example
python weather_data.py
```

## API Reference

The project uses the [Open-Meteo API](https://open-meteo.com/) which provides free weather data without requiring an API key.

## Location

Default coordinates are set for Shenzhen, China:
- Latitude: 22.5431°N
- Longitude: 114.0579°E

## Requirements

- Python 3.7+
- pandas >= 1.5.0
- requests >= 2.25.0
- numpy >= 1.21.0
- scipy >= 1.7.0
