#!/usr/bin/env python3
import sys
import os
sys.path.append('/Users/surjithsshetty/Desktop/smart_traffic_project')

from ml_models import TrafficPredictor

def test_prediction():
    """Test the prediction functionality"""
    try:
        predictor = TrafficPredictor()
        
        if not predictor.load_models():
            print("Training models...")
            predictor.load_data('traffic_data.csv')
            predictor.train_all_models()
            predictor.save_models()
        
        predicted_traffic = predictor.predict_traffic(
            hour=8, day_of_week=1, is_weekend=0, rain_intensity=0.0,
            temperature=25, humidity=60, event_flag=0, rush_hour=1, avg_speed=35
        )
        
        route_score = predictor.calculate_route_score(
            predicted_traffic=predicted_traffic, avg_speed=35, 
            rain_intensity=0.0, event_impact=0.0
        )
        
        print("Prediction Test Results:")
        print(f"   Traffic Flow: {predicted_traffic:.0f} vehicles/hour")
        print(f"   Route Score: {route_score:.1f}/100")
        
        return True
        
    except Exception as e:
        print(f"Prediction Error: {e}")
        return False

if __name__ == "__main__":
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project')
    test_prediction()
