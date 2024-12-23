
from fastapi.testclient import TestClient
from server import app

def test_canary_check():
    client = TestClient(app)
    response = client.get("/canary")
    assert response.status_code == 200
    assert response.json() == {"status": "alive", "message": "Canary check successful"}
