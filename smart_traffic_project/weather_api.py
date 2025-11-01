import requests
import json
from datetime import datetime

class WeatherAPI:
    def __init__(self, api_key=None):
        # Using a demo API key - replace with your own for production
        self.api_key = api_key or "demo_key"
        self.base_url = "http://api.openweathermap.org/data/2.5/weather"
    
    def get_weather_data(self, city="Bangalore"):
        """Get current weather data for a city"""
        try:
            if self.api_key == "demo_key":
                # Return mock data for demo purposes
                return self._get_mock_weather_data()
            
            params = {
                'q': city,
                'appid': self.api_key,
                'units': 'metric'
            }
            
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                return self._parse_weather_data(data)
            else:
                print(f"Error fetching weather data: {response.status_code}")
                return self._get_mock_weather_data()
                
        except Exception as e:
            print(f"Weather API error: {e}")
            return self._get_mock_weather_data()
    
    def _parse_weather_data(self, data):
        """Parse OpenWeatherMap API response"""
        try:
            weather_info = {
                'temperature': data['main']['temp'],
                'humidity': data['main']['humidity'],
                'rain_intensity': 0.0,
                'weather_description': data['weather'][0]['description'],
                'city': data['name']
            }
            
            # Check for rain data
            if 'rain' in data:
                if '1h' in data['rain']:
                    weather_info['rain_intensity'] = min(data['rain']['1h'] / 10, 1.0)
                elif '3h' in data['rain']:
                    weather_info['rain_intensity'] = min(data['rain']['3h'] / 30, 1.0)
            
            return weather_info
            
        except Exception as e:
            print(f"Error parsing weather data: {e}")
            return self._get_mock_weather_data()
    
    def _get_mock_weather_data(self):
        """Return mock weather data for demo"""
        import random
        
        # Generate realistic weather data
        current_hour = datetime.now().hour
        
        # Temperature varies by time of day
        if 6 <= current_hour <= 10:
            temp_base = 22
        elif 11 <= current_hour <= 15:
            temp_base = 28
        elif 16 <= current_hour <= 19:
            temp_base = 26
        else:
            temp_base = 20
            
        temperature = temp_base + random.uniform(-3, 3)
        humidity = random.uniform(40, 85)
        rain_intensity = random.choice([0.0, 0.0, 0.0, 0.1, 0.3, 0.6])  # Mostly no rain
        
        descriptions = [
            "Clear sky", "Few clouds", "Scattered clouds", 
            "Broken clouds", "Light rain", "Moderate rain"
        ]
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'rain_intensity': rain_intensity,
            'weather_description': random.choice(descriptions),
            'city': 'Demo City'
        }

# Example usage
if __name__ == "__main__":
    weather = WeatherAPI()
    data = weather.get_weather_data("Bangalore")
    print("Current Weather Data:")
    for key, value in data.items():
        print(f"{key}: {value}")