import pandas as pd
import numpy as np
from datetime import datetime, timedelta
import random

def generate_traffic_dataset(num_records=5000):
    """Generate realistic traffic dataset with weather and event data"""
    
    np.random.seed(42)
    random.seed(42)
    
    data = []
    start_date = datetime(2023, 1, 1)
    
    for i in range(num_records):
        # Time features
        current_time = start_date + timedelta(hours=i/10)
        hour = current_time.hour
        day_of_week = current_time.weekday()  # 0=Monday, 6=Sunday
        is_weekend = 1 if day_of_week >= 5 else 0
        
        # Weather features
        rain_intensity = max(0, np.random.normal(0.2, 0.3))
        temperature = np.random.normal(25, 8)
        humidity = np.random.uniform(30, 90)
        
        # Event features
        event_flag = 1 if random.random() < 0.1 else 0  # 10% chance of event
        
        # Rush hour patterns
        rush_hour = 1 if (7 <= hour <= 9) or (17 <= hour <= 19) else 0
        
        # Base traffic calculation with realistic patterns
        base_traffic = 200
        
        # Hour effect (rush hours have more traffic)
        if 7 <= hour <= 9:
            hour_multiplier = 2.5
        elif 17 <= hour <= 19:
            hour_multiplier = 2.8
        elif 10 <= hour <= 16:
            hour_multiplier = 1.5
        elif 20 <= hour <= 22:
            hour_multiplier = 1.2
        else:
            hour_multiplier = 0.5
            
        # Weekend effect (less traffic)
        weekend_multiplier = 0.7 if is_weekend else 1.0
        
        # Weather effect (rain increases traffic)
        rain_multiplier = 1 + (rain_intensity * 0.8)
        
        # Event effect
        event_multiplier = 1.5 if event_flag else 1.0
        
        # Calculate traffic flow
        traffic_flow = base_traffic * hour_multiplier * weekend_multiplier * rain_multiplier * event_multiplier
        traffic_flow += np.random.normal(0, 30)  # Add noise
        traffic_flow = max(50, traffic_flow)  # Minimum traffic
        
        # Calculate average speed (inversely related to traffic)
        max_speed = 60
        avg_speed = max_speed * (1 - min(traffic_flow/800, 0.8)) + np.random.normal(0, 5)
        avg_speed = max(10, min(avg_speed, max_speed))
        
        data.append({
            'hour': hour,
            'day_of_week': day_of_week,
            'is_weekend': is_weekend,
            'rain_intensity': round(rain_intensity, 2),
            'temperature': round(temperature, 1),
            'humidity': round(humidity, 1),
            'event_flag': event_flag,
            'rush_hour': rush_hour,
            'avg_speed': round(avg_speed, 1),
            'traffic_flow': round(traffic_flow, 0)
        })
    
    return pd.DataFrame(data)

if __name__ == "__main__":
    df = generate_traffic_dataset()
    df.to_csv('/Users/surjithsshetty/Desktop/smart_traffic_project/traffic_data.csv', index=False)
    print(f"Generated dataset with {len(df)} records")
    print(df.head())
    print(f"\nDataset shape: {df.shape}")
    print(f"Traffic flow range: {df['traffic_flow'].min():.0f} - {df['traffic_flow'].max():.0f}")