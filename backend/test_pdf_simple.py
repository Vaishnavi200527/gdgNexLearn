#!/usr/bin/env python3
"""
Simple test for PDF upload functionality
"""
import requests

# Test with the educational PDF we created
url = "http://localhost:8000/pdf-upload/process-pdf"

try:
    with open("test_educational.pdf", "rb") as f:
        files = {"file": ("test_educational.pdf", f, "application/pdf")}
        data = {"assignment_title": "Machine Learning Test"}
        response = requests.post(url, files=files, data=data)

    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")

except Exception as e:
    print(f"Error: {e}")
