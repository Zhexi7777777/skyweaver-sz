"""
Test script with mock data for weather data functionality.
"""

import sys
import os
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_data import SkyWeaverWeatherData


def create_mock_weather_data() -> pd.DataFrame:
    """Create mock weather data for testing."""
    # Create 6 days of hourly data (144 hours)
    hours = 6 * 24
    
    # Generate datetime index for past 5 days + next 1 day
    end_time = datetime.now().replace(minute=0, second=0, microsecond=0) + timedelta(days=1)
    start_time = end_time - timedelta(days=6)
    datetime_index = pd.date_range(start=start_time, end=end_time, freq='h')[:-1]  # Remove last to get exactly 144 hours
    
    # Generate realistic weather data for Shenzhen
    np.random.seed(42)  # For reproducible results
    
    # Temperature: 20-35°C with daily cycles
    base_temp = 27
    daily_cycle = 5 * np.sin(2 * np.pi * np.arange(hours) / 24)
    temp_noise = np.random.normal(0, 2, hours)
    temperature = base_temp + daily_cycle + temp_noise
    
    # Humidity: 60-90% with some variation
    base_humidity = 75
    humidity_noise = np.random.normal(0, 10, hours)
    humidity = np.clip(base_humidity + humidity_noise, 40, 100)
    
    # Wind speed: 0-15 m/s
    wind_speed = np.abs(np.random.normal(5, 3, hours))
    wind_speed = np.clip(wind_speed, 0, 15)
    
    # Cloud cover: 0-100%
    cloud_cover = np.abs(np.random.normal(50, 25, hours))
    cloud_cover = np.clip(cloud_cover, 0, 100)
    
    # Create DataFrame
    weather_df = pd.DataFrame({
        'temperature': temperature,
        'humidity': humidity,
        'wind_speed': wind_speed,
        'cloud_cover': cloud_cover
    }, index=datetime_index)
    
    weather_df.index.name = 'datetime_utc'
    
    return weather_df


def test_weather_data_structure():
    """Test weather data structure and basic properties."""
    print("Testing weather data structure...")
    
    try:
        weather_df = create_mock_weather_data()
        
        # Basic validation
        assert isinstance(weather_df, pd.DataFrame), "Should return a pandas DataFrame"
        assert not weather_df.empty, "DataFrame should not be empty"
        assert len(weather_df) > 0, "Should have data points"
        
        # Check required columns
        required_columns = ['temperature', 'humidity', 'wind_speed', 'cloud_cover']
        for col in required_columns:
            assert col in weather_df.columns, f"Missing column: {col}"
        
        # Check index is datetime
        assert isinstance(weather_df.index, pd.DatetimeIndex), "Index should be DatetimeIndex"
        
        # Check we have roughly 6 days of hourly data (144 hours)
        expected_hours = 6 * 24  # 6 days
        actual_hours = len(weather_df)
        assert actual_hours == expected_hours, f"Expected {expected_hours} hours, got {actual_hours}"
        
        print(f"✓ Weather data structure test passed!")
        print(f"  - Data points: {len(weather_df)}")
        print(f"  - Date range: {weather_df.index.min()} to {weather_df.index.max()}")
        print(f"  - Columns: {list(weather_df.columns)}")
        
        return weather_df
        
    except Exception as e:
        print(f"✗ Weather data structure test failed: {e}")
        raise


def test_normalization():
    """Test normalization functionality."""
    print("\nTesting normalization...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        
        # Test data
        test_series = pd.Series([10, 20, 30, 40, 50])
        
        # Test default normalization (0 to 1)
        normalized = skyweaver.normalize_values(test_series)
        assert abs(normalized.min() - 0.0) < 0.001, "Min should be 0"
        assert abs(normalized.max() - 1.0) < 0.001, "Max should be 1"
        
        # Test custom range normalization
        normalized_custom = skyweaver.normalize_values(test_series, (0.2, 0.8))
        assert abs(normalized_custom.min() - 0.2) < 0.001, "Min should be 0.2"
        assert abs(normalized_custom.max() - 0.8) < 0.001, "Max should be 0.8"
        
        # Test constant values
        constant_series = pd.Series([5, 5, 5, 5, 5])
        normalized_constant = skyweaver.normalize_values(constant_series)
        assert all(normalized_constant == 0.0), "Constant values should normalize to min"
        
        print(f"✓ Normalization test passed!")
        
    except Exception as e:
        print(f"✗ Normalization test failed: {e}")
        raise


def test_smoothing():
    """Test time series smoothing."""
    print("\nTesting smoothing...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        
        # Create noisy test data
        np.random.seed(42)
        test_data = np.sin(np.linspace(0, 4*np.pi, 100)) + 0.3 * np.random.randn(100)
        test_series = pd.Series(test_data)
        
        # Apply smoothing
        smoothed = skyweaver.smooth_time_series(test_series, sigma=2.0)
        
        # Check that smoothing reduces variance
        original_var = test_series.var()
        smoothed_var = smoothed.var()
        assert smoothed_var < original_var, "Smoothing should reduce variance"
        
        # Check that length is preserved
        assert len(smoothed) == len(test_series), "Length should be preserved"
        
        print(f"✓ Smoothing test passed!")
        print(f"  - Original variance: {original_var:.4f}")
        print(f"  - Smoothed variance: {smoothed_var:.4f}")
        
    except Exception as e:
        print(f"✗ Smoothing test failed: {e}")
        raise


def test_visualization_mapping():
    """Test weather to visualization parameter mapping."""
    print("\nTesting visualization mapping...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        weather_df = create_mock_weather_data()
        viz_df = skyweaver.map_weather_to_visualization(weather_df)
        
        # Basic validation
        assert isinstance(viz_df, pd.DataFrame), "Should return a pandas DataFrame"
        assert len(viz_df) == len(weather_df), "Should have same number of rows as input"
        
        # Check required columns
        required_columns = ['terrain_amplitude', 'horizontal_drift_speed', 'gamma_haze', 'color_warmth']
        for col in required_columns:
            assert col in viz_df.columns, f"Missing column: {col}"
        
        # Check normalization (values should be between 0 and 1, with some exceptions for terrain_amplitude)
        for col in viz_df.columns:
            col_min, col_max = viz_df[col].min(), viz_df[col].max()
            if col == 'terrain_amplitude':
                assert col_min >= 0.0 and col_max <= 1.0, f"{col} values out of expected range"
            else:
                assert col_min >= 0.0 and col_max <= 1.0, f"{col} values should be normalized [0,1]"
        
        # Check that values are not constant (should have variation)
        for col in viz_df.columns:
            assert viz_df[col].std() > 0.01, f"{col} should have some variation"
        
        print(f"✓ Visualization mapping test passed!")
        print(f"  - Generated {len(viz_df)} mapped data points")
        print(f"  - Columns: {list(viz_df.columns)}")
        print(f"  - Value ranges:")
        for col in viz_df.columns:
            print(f"    {col}: [{viz_df[col].min():.3f}, {viz_df[col].max():.3f}] (std: {viz_df[col].std():.3f})")
        
        return viz_df
        
    except Exception as e:
        print(f"✗ Visualization mapping test failed: {e}")
        raise


def test_parameter_relationships():
    """Test that parameter mappings make sense."""
    print("\nTesting parameter relationships...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        weather_df = create_mock_weather_data()
        viz_df = skyweaver.map_weather_to_visualization(weather_df)
        
        # Test correlations (should be positive for all mappings)
        temp_amplitude_corr = weather_df['temperature'].corr(viz_df['terrain_amplitude'])
        wind_drift_corr = weather_df['wind_speed'].corr(viz_df['horizontal_drift_speed'])
        cloud_haze_corr = weather_df['cloud_cover'].corr(viz_df['gamma_haze'])
        humidity_warmth_corr = weather_df['humidity'].corr(viz_df['color_warmth'])
        
        assert temp_amplitude_corr > 0.5, f"Temperature-amplitude correlation too low: {temp_amplitude_corr:.3f}"
        assert wind_drift_corr > 0.5, f"Wind-drift correlation too low: {wind_drift_corr:.3f}"
        assert cloud_haze_corr > 0.5, f"Cloud-haze correlation too low: {cloud_haze_corr:.3f}"
        assert humidity_warmth_corr > 0.5, f"Humidity-warmth correlation too low: {humidity_warmth_corr:.3f}"
        
        print(f"✓ Parameter relationships test passed!")
        print(f"  - Temperature → Terrain Amplitude correlation: {temp_amplitude_corr:.3f}")
        print(f"  - Wind Speed → Horizontal Drift correlation: {wind_drift_corr:.3f}")
        print(f"  - Cloud Cover → Gamma Haze correlation: {cloud_haze_corr:.3f}")
        print(f"  - Humidity → Color Warmth correlation: {humidity_warmth_corr:.3f}")
        
    except Exception as e:
        print(f"✗ Parameter relationships test failed: {e}")
        raise


def demonstrate_functionality():
    """Demonstrate the complete functionality with mock data."""
    print("\nDemonstrating complete functionality...")
    
    try:
        # Use mock data to simulate the complete workflow
        skyweaver = SkyWeaverWeatherData()
        weather_df = create_mock_weather_data()
        viz_df = skyweaver.map_weather_to_visualization(weather_df)
        
        print(f"✓ Complete workflow demonstration passed!")
        print(f"  - Weather data shape: {weather_df.shape}")
        print(f"  - Visualization data shape: {viz_df.shape}")
        
        # Show sample data
        print("\nSample Weather Data:")
        print(weather_df.head(3).round(2))
        
        print("\nSample Visualization Parameters:")
        print(viz_df.head(3).round(3))
        
        print("\nWeather Data Statistics:")
        print(weather_df.describe().round(2))
        
        print("\nVisualization Parameters Statistics:")
        print(viz_df.describe().round(3))
        
        return weather_df, viz_df
        
    except Exception as e:
        print(f"✗ Complete workflow demonstration failed: {e}")
        raise


def main():
    """Run all tests."""
    print("=" * 60)
    print("SkyWeaver Weather Data Test Suite (Mock Data)")
    print("=" * 60)
    
    try:
        # Test 1: Weather data structure
        weather_df = test_weather_data_structure()
        
        # Test 2: Normalization
        test_normalization()
        
        # Test 3: Smoothing
        test_smoothing()
        
        # Test 4: Visualization mapping
        viz_df = test_visualization_mapping()
        
        # Test 5: Parameter relationships
        test_parameter_relationships()
        
        # Test 6: Complete demonstration
        demonstrate_functionality()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        
        print("\nNote: This test used mock data. To use real Open-Meteo API data:")
        print("1. Ensure internet connectivity")
        print("2. Run: python weather_data.py")
        print("3. Or use: SkyWeaverWeatherData().get_weather_visualization_data()")
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ Tests failed: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()