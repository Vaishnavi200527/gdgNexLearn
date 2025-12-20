#!/usr/bin/env python3
"""
Script to run the EduAI Platform server
"""

import sys
import os

# Add the backend directory to the Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

if __name__ == "__main__":
    try:
        # Change to the backend directory
        os.chdir(os.path.join(os.path.dirname(__file__), 'backend'))
        
        # Import and run the main application
        from main import app
        import uvicorn
        
        print("Starting EduAI Platform server...")
        print("Visit http://localhost:8000 for the API")
        print("Visit http://localhost:8000/docs for API documentation")
        
        uvicorn.run(app, host="0.0.0.0", port=8000)
        
    except Exception as e:
        print(f"Error starting server: {e}")
        import traceback
        traceback.print_exc()