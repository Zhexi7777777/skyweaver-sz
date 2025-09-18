"""
Test script for weather data functionality.
"""

import sys
import os

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_data import SkyWeaverWeatherData
import pandas as pd


def test_weather_data_fetching():
    """Test weather data fetching functionality."""
    print("Testing weather data fetching...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        weather_df = skyweaver.fetch_weather_data()
        
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
        assert abs(actual_hours - expected_hours) <= 24, f"Expected ~{expected_hours} hours, got {actual_hours}"
        
        print(f"✓ Weather data fetching test passed!")
        print(f"  - Fetched {len(weather_df)} data points")
        print(f"  - Date range: {weather_df.index.min()} to {weather_df.index.max()}")
        print(f"  - Columns: {list(weather_df.columns)}")
        
        return weather_df
        
    except Exception as e:
        print(f"✗ Weather data fetching test failed: {e}")
        raise


def test_visualization_mapping(weather_df):
    """Test weather to visualization parameter mapping."""
    print("\nTesting visualization mapping...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
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
        
        print(f"✓ Visualization mapping test passed!")
        print(f"  - Generated {len(viz_df)} mapped data points")
        print(f"  - Columns: {list(viz_df.columns)}")
        print(f"  - Value ranges:")
        for col in viz_df.columns:
            print(f"    {col}: [{viz_df[col].min():.3f}, {viz_df[col].max():.3f}]")
        
        return viz_df
        
    except Exception as e:
        print(f"✗ Visualization mapping test failed: {e}")
        raise


def test_complete_workflow():
    """Test the complete workflow."""
    print("\nTesting complete workflow...")
    
    try:
        skyweaver = SkyWeaverWeatherData()
        weather_df, viz_df = skyweaver.get_weather_visualization_data()
        
        # Basic validation
        assert isinstance(weather_df, pd.DataFrame), "Weather data should be DataFrame"
        assert isinstance(viz_df, pd.DataFrame), "Visualization data should be DataFrame"
        assert len(weather_df) == len(viz_df), "Both DataFrames should have same length"
        
        print(f"✓ Complete workflow test passed!")
        print(f"  - Weather data shape: {weather_df.shape}")
        print(f"  - Visualization data shape: {viz_df.shape}")
        
        return weather_df, viz_df
        
    except Exception as e:
        print(f"✗ Complete workflow test failed: {e}")
        raise


def main():
    """Run all tests."""
    print("=" * 60)
    print("SkyWeaver Weather Data Test Suite")
    print("=" * 60)
    
    try:
        # Test 1: Weather data fetching
        weather_df = test_weather_data_fetching()
        
        # Test 2: Visualization mapping
        viz_df = test_visualization_mapping(weather_df)
        
        # Test 3: Complete workflow
        weather_df_complete, viz_df_complete = test_complete_workflow()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed successfully!")
        print("=" * 60)
        
        # Show sample data
        print("\nSample Weather Data:")
        print(weather_df.head(3))
        
        print("\nSample Visualization Parameters:")
        print(viz_df.head(3))
        
    except Exception as e:
        print("\n" + "=" * 60)
        print(f"✗ Tests failed: {e}")
        print("=" * 60)
        sys.exit(1)


if __name__ == "__main__":
    main()