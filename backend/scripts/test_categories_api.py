import httpx

r = httpx.get('http://127.0.0.1:8000/api/categories')
print(f'Status: {r.status_code}')
cats = r.json()
print(f'Categories: {len(cats["data"])}')
for c in cats['data']:
    print(f'  {c["id"]}: {c["name"]} (sort: {c["sort_order"]})')
