from fastapi.testclient import TestClient
from app.main import app
import urllib.parse

client = TestClient(app)

# filter near future
params = urllib.parse.urlencode({"start_time": "2025-10-01T00:00:00"})
resp = client.get("/inventory/requisitions?" + params)
print("Filtered len:", len(resp.json()))
