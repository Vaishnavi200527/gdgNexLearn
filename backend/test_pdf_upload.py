#!/usr/bin/env python3
"""
Test script for PDF upload functionality
"""
import requests
import json
from pathlib import Path

def test_pdf_upload():
    """Test the PDF upload endpoint"""
    # First, let's create a simple test PDF or use an existing one
    test_pdf_path = Path("test.pdf")

    # If no test PDF exists, we'll create a simple text file for testing
    if not test_pdf_path.exists():
        print("No test.pdf found. Creating a simple test file...")
        with open("test.pdf", "w") as f:
            f.write("This is a test PDF content for testing the upload functionality.")
        print("Test file created.")

    # Test the PDF upload endpoint
    url = "http://localhost:8000/pdf-upload/process-pdf"

    try:
        with open("test.pdf", "rb") as f:
            files = {"file": ("test.pdf", f, "application/pdf")}
            data = {"assignment_title": "Test Assignment"}
            response = requests.post(url, files=files, data=data)

        print(f"Response status: {response.status_code}")
        print(f"Response headers: {response.headers}")

        if response.status_code == 200:
            result = response.json()
            print("Success! Response:")
            print(json.dumps(result, indent=2))
        else:
            print(f"Error: {response.text}")

    except requests.exceptions.ConnectionError:
        print("Connection failed. Is the backend server running?")
    except Exception as e:
        print(f"Test failed with error: {e}")

if __name__ == "__main__":
    test_pdf_upload()
