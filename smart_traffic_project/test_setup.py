#!/usr/bin/env python3
import os
import subprocess
import time
import requests

def test_backend():
    """Test if backend is working"""
    try:
        response = requests.get('http://localhost:5001/api/weather', timeout=5)
        if response.status_code == 200:
            print("Backend API is working!")
            return True
        else:
            print(f"Backend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Backend not responding: {e}")
        return False

def test_frontend():
    """Test if frontend is accessible"""
    try:
        response = requests.get('http://localhost:8080', timeout=5)
        if response.status_code == 200:
            print("Frontend is accessible!")
            return True
        else:
            print(f"Frontend returned status {response.status_code}")
            return False
    except Exception as e:
        print(f"Frontend not responding: {e}")
        return False

def main():
    print("Testing Smart Traffic Flow Predictor Setup")
    print("=" * 50)
    
    required_files = [
        'traffic_data.csv',
        'trained_models.pkl',
        'frontend/index.html',
        'backend/api.py'
    ]
    
    for file in required_files:
        if os.path.exists(file):
            print(f"{file} exists")
        else:
            print(f"{file} missing")
    
    print("\nStarting servers for testing...")
    
    backend_process = subprocess.Popen(
        ['python', 'backend/api.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )
    
    print("Waiting for backend to start...")
    time.sleep(3)
    
    backend_ok = test_backend()
    
    if backend_ok:
        frontend_process = subprocess.Popen(
            ['python', '-m', 'http.server', '8080'],
            cwd='frontend',
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE
        )
        
        print("Waiting for frontend to start...")
        time.sleep(2)
        
        frontend_ok = test_frontend()
        
        if frontend_ok:
            print("\nSUCCESS! Both servers are running:")
            print("Frontend: http://localhost:8080")
            print("Backend API: http://localhost:5001")
            print("\nPress Ctrl+C to stop servers")
            
            try:
                while True:
                    time.sleep(1)
            except KeyboardInterrupt:
                print("\nStopping servers...")
                frontend_process.terminate()
        else:
            print("Frontend failed to start")
    else:
        print("Backend failed to start")
    
    backend_process.terminate()

if __name__ == "__main__":
    main()
