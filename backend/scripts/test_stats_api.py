import httpx

r = httpx.get('http://127.0.0.1:8000/api/items/stats?family_id=2', headers={'X-User-Id': '1'})
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print(f'Data: {r.json()}')
else:
    print(f'Error: {r.text}')
