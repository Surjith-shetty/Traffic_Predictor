from flask import Flask, request, jsonify
from flask_cors import CORS
import random
import math
from weather_api import WeatherAPI

app = Flask(__name__)
CORS(app)
weather_api = WeatherAPI()

@app.route('/api/weather', methods=['GET'])
def get_weather():
    try:
        weather_data = weather_api.get_weather_data()
        return jsonify({'success': True, 'weather': weather_data})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/predict', methods=['POST'])
def predict_traffic():
    try:
        data = request.json
        origin = data.get('origin', 'Start')
        destination = data.get('destination', 'End')
        hour = data.get('hour', 8)
        # Get predicted weather for selected day and hour
        day_of_week = data.get('day_of_week', 1)
        weather_data = weather_api.predict_weather_for_day(day_of_week, hour)
        rain = weather_data['rain_intensity']
        temperature = weather_data['temperature']
        
        speed = data.get('avg_speed', 35)
        event = data.get('event_flag', 0)
        rush_hour = data.get('rush_hour', 0)
        
        # Weather-enhanced traffic calculation
        base_traffic = 200
        if rush_hour:
            base_traffic *= 2.5
        if rain > 0.3:
            base_traffic *= 1.5
        if temperature > 35:
            base_traffic *= 1.2
        if event:
            base_traffic *= 1.3
            
        traffic = base_traffic + random.randint(-50, 50)
        score = max(0, min(100, 100 - (traffic / 10) + (speed / 2)))
        
        if traffic < 200:
            level = {"level": "Light", "color": "#4CAF50", "icon": "🟢"}
        elif traffic < 400:
            level = {"level": "Moderate", "color": "#FF9800", "icon": "🟡"}
        else:
            level = {"level": "Heavy", "color": "#F44336", "icon": "🔴"}
            
        recs = [f"Good conditions for {origin} to {destination}"]
        if score < 50:
            recs = ["Consider alternative routes", "Allow extra time"]
        if rain > 0.3:
            recs.append("Drive carefully due to rain")
            
        return jsonify({
            'success': True,
            'predicted_traffic': int(traffic),
            'route_score': round(score, 1),
            'traffic_level': level,
            'recommendations': recs,
            'route_info': f"{origin} → {destination}"
        })
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/models', methods=['GET'])
def get_models():
    models = [
        {'name': 'Linear Regression', 'mae': 52.97, 'rmse': 72.86, 'r2': 0.8897, 'accuracy': 88.97},
        {'name': 'Random Forest', 'mae': 25.46, 'rmse': 32.79, 'r2': 0.9777, 'accuracy': 97.77}
    ]
    return jsonify({'success': True, 'models': models})

@app.route('/api/routes', methods=['POST'])
def get_routes():
    try:
        data = request.json
        origin = data.get('origin', 'Start')
        destination = data.get('destination', 'End')
        
        # Get weather data for route calculation
        weather_data = weather_api.get_weather_data()
        rain_impact = 1 + (weather_data['rain_intensity'] * 0.3)
        
        routes = [
            {
                'name': f'Route 1 (Main Road) - {origin} to {destination}',
                'distance': '12.5 km', 
                'duration': f"{int(18 * rain_impact)} mins",
                'traffic': int(350 * rain_impact), 
                'score': max(30, 75 - (weather_data['rain_intensity'] * 20)),
                'steps': ['Head north', 'Turn right on Main St', 'Continue straight', 'Arrive at destination']
            },
            {
                'name': f'Route 2 (Highway) - {origin} to {destination}',
                'distance': '15.2 km', 
                'duration': f"{int(16 * rain_impact)} mins",
                'traffic': int(280 * rain_impact), 
                'score': max(40, 85 - (weather_data['rain_intensity'] * 15)),
                'steps': ['Head east', 'Merge onto highway', 'Continue for 12 km', 'Exit and arrive']
            }
        ]
        
        best = max(routes, key=lambda x: x['score'])
        return jsonify({'success': True, 'routes': routes, 'best_route': best})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

if __name__ == '__main__':
    print("Simple Backend Starting...")
    app.run(debug=True, port=5001, host='0.0.0.0')