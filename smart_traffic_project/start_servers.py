#!/usr/bin/env python3
import subprocess
import threading
import time
import webbrowser
import os

def start_backend():
    """Start Flask API server"""
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/backend')
    subprocess.run(['python', 'api.py'])

def start_frontend():
    """Start simple HTTP server for frontend"""
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/frontend')
    subprocess.run(['python', '-m', 'http.server', '8080'])

def main():
    print("🚦 Starting Smart Traffic Flow Predictor")
    print("=" * 50)
    
    # Start backend in a separate thread
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    print("🔧 Backend API starting on http://localhost:5000")
    time.sleep(3)  # Wait for backend to start
    
    # Start frontend in a separate thread
    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    print("🌐 Frontend starting on http://localhost:8080")
    time.sleep(2)
    
    # Open browser
    print("🚀 Opening application in browser...")
    webbrowser.open('http://localhost:8080')
    
    print("\n✅ Application is running!")
    print("📱 Frontend: http://localhost:8080")
    print("🔧 API: http://localhost:5000")
    print("\nPress Ctrl+C to stop")
    
    try:
        # Keep main thread alive
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n👋 Shutting down...")

if __name__ == "__main__":
    main()