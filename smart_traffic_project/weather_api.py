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
    
    def predict_weather_for_day(self, day_of_week, hour):
        """Predict weather based on day and hour"""
        import random
        
        # Day-based weather patterns
        if day_of_week in [5, 6]:  # Weekend
            temp_modifier = random.uniform(-2, 2)
            rain_chance = 0.3
        else:  # Weekday
            temp_modifier = random.uniform(-1, 1)
            rain_chance = 0.2
            
        # Hour-based temperature
        if 6 <= hour <= 10:
            temp_base = 22
        elif 11 <= hour <= 15:
            temp_base = 28
        elif 16 <= hour <= 19:
            temp_base = 26
        else:
            temp_base = 20
            
        temperature = temp_base + temp_modifier
        humidity = random.uniform(45, 80)
        rain_intensity = random.choice([0.0, 0.1, 0.3]) if random.random() < rain_chance else 0.0
        
        descriptions = [
            "Clear sky", "Few clouds", "Scattered clouds", 
            "Broken clouds", "Light rain", "Moderate rain"
        ]
        
        return {
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'rain_intensity': rain_intensity,
            'weather_description': random.choice(descriptions),
            'city': 'AI Predicted Weather'
        }
    
    def _get_mock_weather_data(self):
        """Return mock weather data for demo"""
        return self.predict_weather_for_day(datetime.now().weekday(), datetime.now().hour)

# Example usage
if __name__ == "__main__":
    weather = WeatherAPI()
    data = weather.get_weather_data("Bangalore")
    print("Current Weather Data:")
    for key, value in data.items():
        print(f"{key}: {value}")