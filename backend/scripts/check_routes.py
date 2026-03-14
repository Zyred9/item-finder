import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from main import app

print("Registered routes:")
for route in app.routes:
    if hasattr(route, 'methods') and hasattr(route, 'path'):
        print(f"  {list(route.methods)} {route.path}")
