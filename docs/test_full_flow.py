# -*- coding: utf-8 -*-
import requests

base = "http://localhost:8000"

# 登录
print("1. Logging in...")
r = requests.post(f"{base}/api/auth/login", json={"username": "xiaowu", "password": "xiaowu"})
if r.status_code != 200:
    print(f"Login failed: {r.status_code} - {r.text}")
    exit(1)

token = r.json()["access_token"]
print(f"Token: {token[:50]}...")
headers = {"Authorization": f"Bearer {token}"}

# 测试projects
print("\n2. Testing /api/projects/ ...")
r = requests.get(f"{base}/api/projects/", headers=headers)
print(f"Projects: {r.status_code}")

# 测试deployments
print("\n3. Testing /api/deployments/ ...")
r = requests.get(f"{base}/api/deployments/", headers=headers)
print(f"Deployments: {r.status_code}")
if r.status_code != 200:
    print(f"ERROR: {r.text}")
    print("\nBackend NOT properly restarted!")
    print("Please:")
    print("1. Stop backend (Ctrl+C)")
    print("2. Run: cd backend && run.bat")
else:
    print(f"SUCCESS! Deployments: {len(r.json())}")

