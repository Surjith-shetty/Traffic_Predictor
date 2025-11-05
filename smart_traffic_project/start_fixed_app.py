#!/usr/bin/env python3
import subprocess
import threading
import time
import webbrowser
import os

def start_backend():
    """Start Flask API server"""
    try:
        os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/backend')
        subprocess.run(['python', 'api.py'])
    except Exception as e:
        print(f"Backend error: {e}")

def start_frontend():
    """Start HTTP server for frontend"""
    try:
        os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/frontend')
        subprocess.run(['python', '-m', 'http.server', '8080'])
    except Exception as e:
        print(f"Frontend error: {e}")

def main():
    print(" Smart Traffic Flow Predictor (Fixed Version)")
    print("=" * 50)
    
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project')
    
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    print(" Backend starting on http://localhost:5001")
    time.sleep(3)
    
    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    print(" Frontend starting on http://localhost:8080")
    time.sleep(2)
    
    print(" Opening application...")
    webbrowser.open('http://localhost:8080')
    
    print("\\n Fixed Issues:")
    print(" Live Prediction - Error handling improved")
    print(" Map initialization - Only loads when needed")
    print(" Backend API - Better error responses")
    print("\\n Access: http://localhost:8080")
    print("\\nPress Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n Shutting down...")

if __name__ == "__main__":
    main()
