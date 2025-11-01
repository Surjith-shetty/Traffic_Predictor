#!/usr/bin/env python3
import subprocess
import threading
import time
import webbrowser
import os

def start_backend():
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/backend')
    subprocess.run(['python', 'api.py'])

def start_frontend():
    os.chdir('/Users/surjithsshetty/Desktop/smart_traffic_project/frontend')
    subprocess.run(['python', '-m', 'http.server', '8080'])

def main():
    print("🚦 Starting Working Traffic Predictor")
    print("=" * 40)
    
    # Start backend
    backend_thread = threading.Thread(target=start_backend)
    backend_thread.daemon = True
    backend_thread.start()
    
    print("🔧 Backend starting...")
    time.sleep(3)
    
    # Start frontend
    frontend_thread = threading.Thread(target=start_frontend)
    frontend_thread.daemon = True
    frontend_thread.start()
    
    print("🌐 Frontend starting...")
    time.sleep(2)
    
    print("🚀 Opening application...")
    webbrowser.open('http://localhost:8080')
    
    print("\\n✅ Application running:")
    print("🌐 http://localhost:8080")
    print("\\nPress Ctrl+C to stop")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\\n👋 Stopped")

if __name__ == "__main__":
    main()