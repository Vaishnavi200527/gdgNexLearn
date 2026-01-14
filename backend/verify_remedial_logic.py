import requests
import json
import sys

def verify_remedial_logic():
    print("--- Verifying Adaptive Remediation Logic ---")
    base_url = "http://localhost:8000"

    # 1. Login
    print("\n1. Logging in as student...")
    try:
        resp = requests.post(f"{base_url}/auth/token", data={"username": "alice@example.com", "password": "password123"})
    except requests.exceptions.ConnectionError:
        print("Error: Backend is not running on http://localhost:8000")
        return

    if resp.status_code != 200:
        print(f"Login failed: {resp.text}")
        return
    token = resp.json()["access_token"]
    headers = {"Authorization": f"Bearer {token}"}

    # 2. Submit a failing quiz (Assignment 1)
    print("2. Submitting failing quiz (Score: 0%)...")
    payload = {
        "questions": [{"questionIndex": 0, "correct_answer": "A"}],
        "answers": [{"questionIndex": 0, "answer": "B"}] # Wrong answer
    }

    resp = requests.post(
        f"{base_url}/student/assignments/1/quiz/submit",
        json=payload,
        headers=headers
    )

    if resp.status_code == 200:
        data = resp.json()
        print(f"   Quiz Score: {data.get('score')}%")

        if data.get("remedial_content"):
            print("\n[SUCCESS] Backend returned remedial content:")
            print(json.dumps(data["remedial_content"], indent=2))
        else:
            print("\n[FAILURE] Remedial content missing. Check backend logs for AI errors.")
    else:
        print(f"Error submitting quiz: {resp.text}")

if __name__ == "__main__":
    verify_remedial_logic()
