from flask import Flask, request, jsonify
from flask_cors import CORS
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from ml_models import TrafficPredictor
from weather_api import WeatherAPI
from maps_service import MapsService
import pandas as pd
import numpy as np

app = Flask(__name__)
CORS(app)

# Initialize services
predictor = TrafficPredictor()
weather_api = WeatherAPI()
maps_service = MapsService()

# Load models on startup
try:
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project')
    if not predictor.load_models():
        print("Training models...")
        predictor.load_data('traffic_data.csv')
        predictor.train_all_models()
        predictor.save_models()
    print("Models loaded successfully!")
except Exception as e:
    print(f"Error loading models: {e}")

@app.route('/api/predict', methods=['POST'])
def predict_traffic():
    try:
        data = request.json
        
        predicted_traffic = predictor.predict_traffic(
            data.get('hour', 8), data.get('day_of_week', 1), data.get('is_weekend', 0),
            data.get('rain_intensity', 0.0), data.get('temperature', 25), data.get('humidity', 60),
            data.get('event_flag', 0), data.get('rush_hour', 0), data.get('avg_speed', 35)
        )
        
        route_score = predictor.calculate_route_score(
            predicted_traffic, data.get('avg_speed', 35), 
            data.get('rain_intensity', 0.0), 0.3 if data.get('event_flag', 0) else 0.0
        )
        
        traffic_level = get_traffic_level(predicted_traffic)
        recommendations = get_recommendations(route_score, data.get('rain_intensity', 0), 
                                           data.get('rush_hour', 0), data.get('event_flag', 0))
        
        return jsonify({
            'success': True,
            'predicted_traffic': round(predicted_traffic, 0),
            'route_score': round(route_score, 1),
            'traffic_level': traffic_level,
            'recommendations': recommendations
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        city = request.args.get('city', 'Bangalore')
        weather_data = weather_api.get_weather_data(city)
        return jsonify({'success': True, 'data': weather_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/models', methods=['GET'])
def get_model_performance():
    try:
        predictor.load_data('traffic_data.csv')
        results = predictor.train_all_models()
        
        model_data = []
        for name, metrics in results.items():
            model_data.append({
                'name': name,
                'mae': round(metrics['MAE'], 2),
                'rmse': round(metrics['RMSE'], 2),
                'r2': round(metrics['R2'], 4),
                'accuracy': round(metrics['R2'] * 100, 1)
            })
        
        feature_importance = predictor.get_feature_importance()
        features = feature_importance.to_dict('records') if feature_importance is not None else []
        
        return jsonify({
            'success': True,
            'models': model_data,
            'feature_importance': features
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

@app.route('/api/routes', methods=['POST'])
def get_routes():
    try:
        data = request.json
        origin = data.get('origin', 'Bangalore')
        destination = data.get('destination', 'Mysore')
        
        routes = maps_service.get_routes(origin, destination)
        
        route_results = []
        for route in routes:
            adjusted_speed = route.get('base_speed', 40) * (1 - data.get('rain_intensity', 0) * 0.3)
            
            predicted_traffic = predictor.predict_traffic(
                data.get('hour', 8), data.get('day_of_week', 1), data.get('is_weekend', 0),
                data.get('rain_intensity', 0), data.get('temperature', 25), data.get('humidity', 60),
                data.get('event_flag', 0), data.get('rush_hour', 0), adjusted_speed
            ) * route.get('traffic_factor', 1.0)
            
            route_score = predictor.calculate_route_score(
                predicted_traffic, adjusted_speed, data.get('rain_intensity', 0),
                0.3 if data.get('event_flag', 0) else 0.0
            )
            
            route_results.append({
                'name': route['name'],
                'distance': route['distance'],
                'duration': route['duration'],
                'traffic': round(predicted_traffic, 0),
                'speed': round(adjusted_speed, 1),
                'score': round(route_score, 1),
                'polyline': route.get('polyline', ''),
                'steps': route.get('steps', [])
            })
        
        best_route = max(route_results, key=lambda x: x['score'])
        
        return jsonify({
            'success': True, 
            'routes': route_results,
            'best_route': best_route,
            'origin': origin,
            'destination': destination
        })
        
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500

def get_traffic_level(traffic):
    traffic = float(traffic)
    if traffic < 200:
        return {"level": "Light", "color": "#4CAF50", "icon": "🟢"}
    elif traffic < 400:
        return {"level": "Moderate", "color": "#FF9800", "icon": "🟡"}
    elif traffic < 600:
        return {"level": "Heavy", "color": "#FF5722", "icon": "🟠"}
    else:
        return {"level": "Very Heavy", "color": "#F44336", "icon": "🔴"}

def get_recommendations(score, rain, rush_hour, event):
    recommendations = []
    if score < 40:
        recommendations.extend(["Consider alternative routes", "Delay travel if possible"])
    if rain > 0.3:
        recommendations.append("Drive carefully due to rain")
    if rush_hour:
        recommendations.append("Peak hour - expect delays")
    if event:
        recommendations.append("Event traffic - plan extra time")
    if not recommendations:
        recommendations.append("Good conditions for travel")
    return recommendations

if __name__ == '__main__':
    app.run(debug=True, port=5001)