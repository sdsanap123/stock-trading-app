#!/usr/bin/env python3
"""
Run script for Enhanced Swing Trading App - Web Version
"""

import subprocess
import sys
import os

def main():
    """Run the Streamlit application."""
    try:
        # Check if streamlit is installed
        try:
            import streamlit
        except ImportError:
            print("❌ Streamlit not found. Installing requirements...")
            subprocess.check_call([sys.executable, "-m", "pip", "install", "-r", "requirements.txt"])
        
        # Run the application
        print("🚀 Starting Enhanced Swing Trading App - Web Version...")
        print("📱 Open your browser and go to: http://localhost:8501")
        print("🛑 Press Ctrl+C to stop the application")
        
        subprocess.run([
            sys.executable, "-m", "streamlit", "run", "app.py",
            "--server.port=8501",
            "--server.address=localhost",
            "--browser.gatherUsageStats=false"
        ])
        
    except KeyboardInterrupt:
        print("\n🛑 Application stopped by user")
    except Exception as e:
        print(f"❌ Error running application: {str(e)}")
        print("💡 Make sure all dependencies are installed: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
