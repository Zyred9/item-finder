import httpx
import json

r = httpx.get(
    'http://127.0.0.1:8000/api/items?family_id=2&limit=5',
    headers={'X-User-Id': '1'}
)
d = r.json()
print(f"Total: {d['data']['total']}")
print("\nFirst 3 items:")
for i in d['data']['items'][:3]:
    ext = i.get('extension')
    expire = ext.get('expire_date') if ext else None
    print(f"  {i['name']}: expire_date={expire}")
