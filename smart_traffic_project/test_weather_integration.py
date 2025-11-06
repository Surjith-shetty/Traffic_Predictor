#!/usr/bin/env python3
"""
Test script to verify weather API integration
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from weather_api import WeatherAPI
import json

def test_weather_api():
    """Test the weather API functionality"""
    print("🌤️  Testing Weather API Integration")
    print("=" * 50)
    
    # Initialize weather API
    weather_api = WeatherAPI()
    
    # Test getting weather data
    print("📍 Fetching weather data for Bangalore...")
    weather_data = weather_api.get_weather_data("Bangalore")
    
    print("\n🌡️  Current Weather Data:")
    print(f"   Temperature: {weather_data['temperature']}°C")
    print(f"   Humidity: {weather_data['humidity']}%")
    print(f"   Rain Intensity: {weather_data['rain_intensity']}")
    print(f"   Description: {weather_data['weather_description']}")
    print(f"   City: {weather_data['city']}")
    
    # Test different cities
    cities = ["Mumbai", "Chennai", "Delhi"]
    print(f"\n🌍 Testing other cities:")
    
    for city in cities:
        try:
            data = weather_api.get_weather_data(city)
            print(f"   {city}: {data['temperature']}°C, {data['weather_description']}")
        except Exception as e:
            print(f"   {city}: Error - {e}")
    
    # Test JSON serialization
    print(f"\n📄 JSON Output:")
    print(json.dumps(weather_data, indent=2))
    
    print(f"\n✅ Weather API integration test completed!")
    print(f"   The weather data will be automatically used in traffic predictions.")

if __name__ == "__main__":
    test_weather_api()