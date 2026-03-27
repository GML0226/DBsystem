from fastapi.testclient import TestClient
from app.main import app
import urllib.parse

client = TestClient(app)

# filter near future 
params = urllib.parse.urlencode({"start_time": "2026-03-01T00:00:00Z"})
resp = client.get("/equipment/reservations/all?" + params)
print("Filtered len (>= 2026-03-01):", len(resp.json()))

params = urllib.parse.urlencode({"end_time": "2025-01-01T00:00:00Z"})
resp = client.get("/equipment/reservations/all?" + params)
print("Filtered len (<= 2025-01-01):", len(resp.json()))
