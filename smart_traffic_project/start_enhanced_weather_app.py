#!/usr/bin/env python3
"""
Enhanced Smart Traffic System with Automatic Weather Integration
Starts the backend server with real-time weather predictions
"""

import subprocess
import sys
import os
import time
import webbrowser
from threading import Thread

def print_banner():
    """Print startup banner"""
    print("🚦" + "=" * 60 + "🚦")
    print("    SMART TRAFFIC FLOW PREDICTOR - ENHANCED")
    print("         🌤️  Real-Time Weather Integration")
    print("=" * 64)
    print()
    print("✨ NEW FEATURES:")
    print("   🌡️  Automatic weather data fetching")
    print("   🌧️  Real-time rain and temperature impact")
    print("   🎯  AI-powered weather-based predictions")
    print("   📊  Enhanced route scoring with weather")
    print()

def check_dependencies():
    """Check if required packages are installed"""
    required_packages = ['flask', 'flask-cors', 'requests']
    missing = []
    
    for package in required_packages:
        try:
            __import__(package.replace('-', '_'))
        except ImportError:
            missing.append(package)
    
    if missing:
        print(f"❌ Missing packages: {', '.join(missing)}")
        print(f"   Install with: pip install {' '.join(missing)}")
        return False
    
    print("✅ All dependencies are installed")
    return True

def start_backend():
    """Start the Flask backend server"""
    print("🚀 Starting enhanced backend server...")
    try:
        # Change to the project directory
        os.chdir(os.path.dirname(os.path.abspath(__file__)))
        
        # Start the backend
        subprocess.run([sys.executable, 'simple_backend.py'], check=True)
    except KeyboardInterrupt:
        print("\\n🛑 Server stopped by user")
    except Exception as e:
        print(f"❌ Error starting backend: {e}")

def open_browser():
    """Open the web browser after a delay"""
    time.sleep(3)  # Wait for server to start
    try:
        webbrowser.open('http://localhost:5001')
        print("🌐 Opening web browser...")
    except Exception as e:
        print(f"⚠️  Could not open browser automatically: {e}")
        print("   Please open http://localhost:5001 manually")

def main():
    """Main function"""
    print_banner()
    
    if not check_dependencies():
        return
    
    print("🔧 System Configuration:")
    print("   Backend: Flask (Port 5001)")
    print("   Frontend: HTML/CSS/JavaScript")
    print("   Weather: OpenWeatherMap API (Demo Mode)")
    print("   AI Models: Traffic prediction with weather impact")
    print()
    
    print("📋 Usage Instructions:")
    print("   1. Enter source and destination locations")
    print("   2. Weather data is automatically fetched and applied")
    print("   3. Get AI-powered traffic predictions with weather impact")
    print("   4. View real-time route recommendations")
    print()
    
    # Start browser in a separate thread
    browser_thread = Thread(target=open_browser)
    browser_thread.daemon = True
    browser_thread.start()
    
    print("🎯 Starting Smart Traffic System...")
    print("   Press Ctrl+C to stop the server")
    print("   Access the app at: http://localhost:5001")
    print()
    
    # Start the backend server
    start_backend()

if __name__ == "__main__":
    main()