#!/usr/bin/env python3
"""
Test script to verify that all imports work correctly
"""

try:
    print("Testing imports...")
    
    # Test importing from routers
    from routers import (
        auth,
        student,
        teacher, 
        classes, 
        notifications,
        quiz,
        ai_content,
        continuous_assessment,
        teacher_dashboard
    )
    print("✅ All router imports successful")
    
    # Test importing main app
    import main
    print("✅ Main app import successful")
    
    print("All imports working correctly!")
    
except Exception as e:
    print(f"❌ Import error: {e}")
    import traceback
    traceback.print_exc()