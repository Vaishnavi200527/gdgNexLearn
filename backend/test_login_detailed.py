import requests

# Test the login endpoint with more detailed output
def test_login():
    try:
        print("Attempting login...")
        response = requests.post(
            "http://localhost:8000/auth/token",
            data={
                "username": "dishakulkarni2005@gmail.com",
                "password": "abcd1234"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        
        print(f"Status Code: {response.status_code}")
        print(f"Response Headers: {dict(response.headers)}")
        print(f"Response Text: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"Login successful! Token: {data.get('access_token', 'No token')[:50]}...")
            print(f"Role: {data.get('role', 'No role')}")
        else:
            print("Login failed")
            # Try to parse error details
            try:
                error_data = response.json()
                print(f"Error details: {error_data}")
            except:
                print("Could not parse error response as JSON")
                
    except requests.exceptions.ConnectionError:
        print("Could not connect to server. Is it running on http://localhost:8000?")
    except Exception as e:
        print(f"Error connecting to server: {e}")

if __name__ == "__main__":
    test_login()