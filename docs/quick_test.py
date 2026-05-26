import requests
import sys

# 测试后端是否运行
try:
    r = requests.get("http://localhost:8000/health", timeout=2)
    print(f"Backend is running: {r.status_code}")
    print(f"Response: {r.json()}")
except Exception as e:
    print(f"Backend is NOT running: {e}")
    sys.exit(1)

# 测试deployments端点
print("\nTesting deployments endpoint...")
try:
    # 不带token访问，应该返回401
    r = requests.get("http://localhost:8000/api/deployments/", timeout=2)
    print(f"Status: {r.status_code}")
    if r.status_code == 401:
        print("Good! Endpoint exists and requires authentication")
    elif r.status_code == 404:
        print("ERROR! Endpoint not found - backend not restarted?")
    print(f"Response: {r.text}")
except Exception as e:
    print(f"Error: {e}")

