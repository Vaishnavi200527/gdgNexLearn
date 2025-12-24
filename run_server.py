import subprocess
import sys
import os
from pathlib import Path

def setup_database():
    """Set up the database by creating tables and seeding with default data"""
    print("Setting up database...")
    
    # Check if database file exists
    db_path = Path("backend/amep.db")
    if not db_path.exists():
        print("Database file not found, creating new database...")
        
        # Import and run database reset
        import backend.database_reset
        backend.database_reset.reset_database()
        
        # Import and run seed data
        import backend.seed_data
        backend.seed_data.seed_database()
    else:
        print("Database file already exists.")

def run_server():
    """Run the FastAPI server"""
    setup_database()
    
    # Run the FastAPI server
    import uvicorn
    sys.path.append('backend')
    import backend.main
    uvicorn.run(backend.main.app, host="0.0.0.0", port=8000)

if __name__ == "__main__":
    run_server()