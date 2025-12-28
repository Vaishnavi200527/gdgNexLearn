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
    
    # Check if database file exists
    db_path = Path("backend/learning.db")
    if not db_path.exists():
        print("Database file not found, creating new database...")
        
        # Import and run database reset
        from backend.database_reset import reset_database
        reset_database()
        
        # Import and run seed data
        from backend.seed_data import seed_database
        seed_database()
    else:
        print("Database file already exists.")
        
        # Always run seed data to ensure data exists
        from backend.seed_data import seed_database
        seed_database()

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