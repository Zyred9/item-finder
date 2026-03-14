import httpx

BASE_URL = "http://127.0.0.1:8000"
HEADERS = {"X-User-Id": "1"}

endpoints = [
    "/api/items/stats?family_id=2",
    "/api/items?family_id=2&limit=10",
    "/api/categories",
    "/api/reminders?family_id=2&status=pending",
    "/api/families/2",
]

print(f"Testing APIs at {BASE_URL}\n")

for endpoint in endpoints:
    try:
        r = httpx.get(f"{BASE_URL}{endpoint}", headers=HEADERS, timeout=2.0)
        status = "[OK]" if r.status_code == 200 else "[ERR]"
        print(f"{status} {endpoint}")
        print(f"   Status: {r.status_code}")
        if r.status_code != 200:
            print(f"   Error: {r.json() if r.headers.get('content-type') == 'application/json' else r.text[:100]}")
    except Exception as e:
        print(f"[ERR] {endpoint}")
        print(f"   Error: {e}")
    print()
