from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def test_health_endpoint():
    response = client.get("/api/v1/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


def test_publications_endpoint_returns_demo_records():
    response = client.get("/api/v1/publications")
    assert response.status_code == 200
    payload = response.json()
    assert payload["total"] >= 1
    assert all("id" in item and "title" in item for item in payload["items"])


def test_publications_can_be_filtered():
    response = client.get("/api/v1/publications", params={"country": "India"})
    assert response.status_code == 200
    assert all(item["country"] == "India" for item in response.json()["items"])
