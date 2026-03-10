import sys
sys.stdout.reconfigure(encoding='utf-8')

from fastapi.testclient import TestClient
from main import app

client = TestClient(app)
response = client.post('/api/auth/login', json={'code': 'test123'})
print('Status:', response.status_code)
print('Body:', response.text)