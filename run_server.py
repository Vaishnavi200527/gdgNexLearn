import subprocess
import sys
import os
from pathlib import Path

def setup_database():
    """Set up the database by creating tables and seeding with default data"""
    print("Setting up database...")
    
    # Add backend to Python path
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_path)
    
    # Import and run database reset and seeding
    print("Clearing and re-seeding database...")
    from backend.clear_db import clear_data
    from backend.seed_data import seed_database
    
    clear_data()
    seed_database()
    
    print("Database setup complete.")

def run_server():
    """Run the FastAPI server"""
    setup_database()
    
    # Add backend to Python path
    backend_path = os.path.join(os.path.dirname(__file__), 'backend')
    sys.path.insert(0, backend_path)
    
    # Run the FastAPI server
    import uvicorn
    from backend.main import app
    uvicorn.run(app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()