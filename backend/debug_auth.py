import requests
import json
import sys

# Configuration
BASE_URL = "http://localhost:8000"
EMAIL = "2005vaishnavikumbhar@gmail.com"
# You can pass the password as a command line argument: python debug_auth.py mypassword
PASSWORD = sys.argv[1] if len(sys.argv) > 1 else "password123" 

def debug_login():
    print(f"Attempting login for: {EMAIL}")
    print(f"Target URL: {BASE_URL}/auth/token")
    
    try:
        # 1. Login Request
        response = requests.post(
            f"{BASE_URL}/auth/token",
            data={"username": EMAIL, "password": PASSWORD}
        )
        
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("\nLogin Successful! Response Payload:")
            print("-" * 30)
            print(json.dumps(data, indent=2))
            print("-" * 30)
            
            # 2. Check for Role
            if "role" in data:
                print(f"✅ Role found in response: '{data['role']}'")
                if data["role"] == "student":
                    print("Backend is correctly identifying this user as a STUDENT.")
                    print("CONCLUSION: Your Frontend is ignoring this role and redirecting to /teacher/dashboard.")
                else:
                    print(f"WARNING: Backend returned role '{data['role']}'. Check your database user entry.")
            else:
                print("❌ Role NOT found in response.")
                print("CONCLUSION: Frontend doesn't know the user role, so it defaults to Teacher.")
                
            # 3. Test Dashboard Access (Verification)
            token = data.get("access_token")
            headers = {"Authorization": f"Bearer {token}"}
            
            print("\nTesting Access Permissions:")
            teacher_resp = requests.get(f"{BASE_URL}/teacher/dashboard", headers=headers)
            print(f"GET /teacher/dashboard -> {teacher_resp.status_code} ({'Correctly Blocked' if teacher_resp.status_code == 403 else 'Unexpected'})")
            
        else:
            print("Login Failed.")
            print(response.text)
            
    except Exception as e:
        print(f"Error: {e}")
        print("Make sure the server is running on localhost:8000")

if __name__ == "__main__":
    debug_login()