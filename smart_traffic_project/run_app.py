#!/usr/bin/env python3
"""
Smart Traffic Flow Predictor - Launcher Script
Run this to start the application
"""

import subprocess
import sys
import os

def install_requirements():
    """Install required packages"""
    try:
        subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        print("All requirements installed successfully!")
    except subprocess.CalledProcessError:
        print("Error installing requirements. Please install manually:")
        print("pip install -r requirements.txt")
        return False
    return True

def run_streamlit_app():
    """Launch the Streamlit application"""
    try:
        print("Starting Smart Traffic Flow Predictor...")
        print("The app will open in your browser automatically")
        print("If it doesn't open, go to: http://localhost:8501")
        print("\n" + "="*50)
        
        subprocess.run([sys.executable, "-m", "streamlit", "run", "app.py"])
    except KeyboardInterrupt:
        print("\nApplication stopped by user")
    except Exception as e:
        print(f"Error running application: {e}")

def main():
    print("Smart Local Traffic Flow Predictor")
    print("=" * 50)
    
    if not os.path.exists("app.py"):
        print("Please run this script from the project directory")
        return
    
    print("Checking requirements...")
    if not install_requirements():
        return
    
    run_streamlit_app()

if __name__ == "__main__":
    main()
