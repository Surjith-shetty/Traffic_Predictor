#!/usr/bin/env python3
import subprocess
import threading
import time
import webbrowser
import os

def start_backend():
    """Start Flask API server"""
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/backend')
    os.environ['FLASK_ENV'] = 'development'
    subprocess.run(['python', 'api.py'], cwd='/Users/surjithsshetty/Desktop/smart_traffic_project/backend')

def start_frontend():
    """Start HTTP server for frontend"""
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/frontend')
    subprocess.run(['python', '-m', 'http.server', '8080'])

def main():
    print("🚦 Smart Traffic Flow Predictor with Route Planning")
    print("=" * 60)
    
    # Start backend
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    print("🔧 Backend API starting on http://localhost:5001")
    time.sleep(4)
    
    # Start frontend
    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    print("🌐 Frontend starting on http://localhost:8080")
    time.sleep(2)
    
    print("🚀 Opening application...")
    webbrowser.open('http://localhost:8080')
    
    print("\\n✅ Enhanced Application Features:")
    print("📍 Source/Destination Input")
    print("🗺️ Interactive Map with Route Visualization")
    print("🎯 Best Route Highlighting")
    print("📊 Real-time Traffic Predictions")
    print("🌧️ Weather-based Route Scoring")
    print("\\n🌐 Frontend: http://localhost:8080")
    print("🔧 API: http://localhost:5001")
    print("\\nPress Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n👋 Shutting down...")

if __name__ == "__main__":
    main()