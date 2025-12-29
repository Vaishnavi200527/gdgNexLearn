import requests

# Test the login endpoint
try:
    response = requests.post(
        "http://localhost:8000/auth/token",
        data={
            "username": "dishakulkarni2005@gmail.com",
            "password": "abcd1234"
        }
    )
    print(f"Status Code: {response.status_code}")
    print(f"Response: {response.text}")
    if response.status_code == 200:
        data = response.json()
        print(f"Login successful! Token: {data.get('access_token', 'No token')[:50]}...")
    else:
        print("Login failed")
except Exception as e:
    print(f"Error connecting to server: {e}")