import requests
import json

# Login to get token
login_response = requests.post('http://localhost:8000/auth/token', data={
    'username': 'alice@example.com',
    'password': 'password123'
})

print("Login response status:", login_response.status_code)
print("Login response text:", login_response.text)

if login_response.status_code == 200:
    token_data = login_response.json()
    token = token_data.get('access_token')
    print("Token received:", token[:20] + "..." if token else "No token")
    
    if token:
        headers = {
            'Authorization': f'Bearer {token}'
        }
        
        # Test the projects endpoint (should work)
        projects_response = requests.get('http://localhost:8000/student/projects', headers=headers)
        print("\nProjects response status:", projects_response.status_code)
        print("Projects response:", projects_response.text[:200] + "..." if len(projects_response.text) > 200 else projects_response.text)
        
        # Test the specific project endpoint (should now work)
        project_response = requests.get('http://localhost:8000/student/projects/1', headers=headers)
        print("\nProject 1 response status:", project_response.status_code)
        print("Project 1 response:", project_response.text[:200] + "..." if len(project_response.text) > 200 else project_response.text)
else:
    print("Login failed, cannot test authenticated endpoints")