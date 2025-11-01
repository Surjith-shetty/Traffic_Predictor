try:
    import googlemaps
    GOOGLEMAPS_AVAILABLE = True
except ImportError:
    GOOGLEMAPS_AVAILABLE = False
    googlemaps = None

import requests
from datetime import datetime

class MapsService:
    def __init__(self, api_key="demo_key"):
        self.api_key = api_key
        if api_key != "demo_key" and GOOGLEMAPS_AVAILABLE:
            self.gmaps = googlemaps.Client(key=api_key)
        else:
            self.gmaps = None
    
    def get_routes(self, origin, destination):
        """Get multiple route options between origin and destination"""
        if self.gmaps:
            try:
                # Get directions with alternatives
                directions = self.gmaps.directions(
                    origin, destination,
                    mode="driving",
                    alternatives=True,
                    departure_time=datetime.now()
                )
                return self._parse_google_routes(directions)
            except Exception as e:
                print(f"Google Maps API error: {e}")
                return self._get_mock_routes(origin, destination)
        else:
            return self._get_mock_routes(origin, destination)
    
    def _parse_google_routes(self, directions):
        """Parse Google Maps API response"""
        routes = []
        for i, route in enumerate(directions):
            leg = route['legs'][0]
            routes.append({
                'name': f"Route {i+1}",
                'distance': leg['distance']['text'],
                'duration': leg['duration']['text'],
                'distance_value': leg['distance']['value'],
                'duration_value': leg['duration']['value'],
                'polyline': route['overview_polyline']['points'],
                'steps': [step['html_instructions'] for step in leg['steps']],
                'traffic_factor': 1.0 + (i * 0.2)  # Simulate different traffic levels
            })
        return routes
    
    def _get_mock_routes(self, origin, destination):
        """Generate mock routes for demo"""
        routes = [
            {
                'name': f"Route 1 (Main Road) - {origin} to {destination}",
                'distance': "12.5 km",
                'duration': "18 mins",
                'distance_value': 12500,
                'duration_value': 1080,
                'polyline': "mock_polyline_1",
                'steps': [
                    f"Head north from {origin}",
                    "Turn right onto Main Street",
                    "Continue straight for 8 km",
                    f"Turn left to reach {destination}"
                ],
                'traffic_factor': 1.2,
                'base_speed': 45
            },
            {
                'name': f"Route 2 (Highway) - {origin} to {destination}",
                'distance': "15.2 km",
                'duration': "16 mins",
                'distance_value': 15200,
                'duration_value': 960,
                'polyline': "mock_polyline_2",
                'steps': [
                    f"Head east from {origin}",
                    "Merge onto Highway 101",
                    "Continue for 12 km",
                    f"Exit and turn right to {destination}"
                ],
                'traffic_factor': 0.8,
                'base_speed': 60
            },
            {
                'name': f"Route 3 (Local Roads) - {origin} to {destination}",
                'distance': "10.8 km",
                'duration': "22 mins",
                'distance_value': 10800,
                'duration_value': 1320,
                'polyline': "mock_polyline_3",
                'steps': [
                    f"Head south from {origin}",
                    "Turn left onto Local Avenue",
                    "Navigate through residential area",
                    f"Turn right to reach {destination}"
                ],
                'traffic_factor': 1.5,
                'base_speed': 30
            }
        ]
        return routes
    
    def geocode_address(self, address):
        """Convert address to coordinates"""
        if self.gmaps:
            try:
                result = self.gmaps.geocode(address)
                if result:
                    location = result[0]['geometry']['location']
                    return {
                        'lat': location['lat'],
                        'lng': location['lng'],
                        'formatted_address': result[0]['formatted_address']
                    }
            except Exception as e:
                print(f"Geocoding error: {e}")
        
        # Return mock coordinates for demo
        return {
            'lat': 12.9716 + (hash(address) % 100) / 1000,
            'lng': 77.5946 + (hash(address) % 100) / 1000,
            'formatted_address': address
        }