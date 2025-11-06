#!/usr/bin/env python3
"""
Quick launcher for the Smart Traffic Navigation System
"""

import os
import sys
import subprocess
import webbrowser
import time
from pathlib import Path

def start_backend():
    """Start the backend API server"""
    backend_path = Path(__file__).parent / "backend"
    if backend_path.exists():
        print(" Starting backend server...")
        return subprocess.Popen([
            sys.executable, "api.py"
        ], cwd=backend_path)
    return None

def start_frontend():
    """Start the frontend server"""
    frontend_path = Path(__file__).parent / "frontend"
    if frontend_path.exists():
        print(" Starting frontend server...")
        return subprocess.Popen([
            "python", "-m", "http.server", "8080"
        ], cwd=frontend_path)
    return None

def main():
    print(" Smart Traffic Navigation System")
    print("=" * 40)
    
    backend_process = start_backend()
    time.sleep(2)
    
    frontend_process = start_frontend()
    time.sleep(2)
    
    print(" Opening browser...")
    webbrowser.open("http://localhost:8080")
    
    print("\n System ready!")
    print(" Real-time navigation with ML predictions")
    print("  Interactive route planning")
    print(" Live traffic analysis")
    print("\nPress Ctrl+C to stop all servers")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n Shutting down...")
        if backend_process:
            backend_process.terminate()
        if frontend_process:
            frontend_process.terminate()
        print(" All servers stopped")

if __name__ == "__main__":
    main()
