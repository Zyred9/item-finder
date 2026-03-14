import httpx

# 测试局域网地址
r = httpx.get('http://192.168.0.7:8000/api/items/stats?family_id=2', headers={'X-User-Id': '1'}, timeout=5.0)
print(f'Status: {r.status_code}')
if r.status_code == 200:
    print(f'Data: {r.json()}')
else:
    print(f'Error: {r.text}')
