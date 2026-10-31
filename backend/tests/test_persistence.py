from fastapi.testclient import TestClient

from app.main import app

client = TestClient(app)


def upload_text(content: str, filename: str = "circular.txt"):
    return client.post(
        "/api/v1/documents",
        files={"file": (filename, content.encode("utf-8"), "text/plain")},
    )


def test_document_upload_is_persisted_and_retrievable():
    content = (
        "Illustrative AI Governance Circular\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2026-27/900\n"
        "Published on 20/10/2026\n"
        "Regulated entities shall maintain a documented inventory of AI systems used in credit decisions.\n"
        "These requirements are effective from 01/04/2027.\n"
    )
    response = upload_text(content)
    assert response.status_code == 200
    payload = response.json()
    persistence = payload["persistence"]
    assert persistence["persisted"] is True
    assert persistence["duplicate"] is False
    assert persistence["original_file_stored"] is False
    assert persistence["stored_sections"] >= 1
    assert persistence["stored_obligations"] >= 1

    listing = client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    document_id = listing.json()["items"][0]["document_version_id"]

    detail = client.get(f"/api/v1/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["publication"]["title"] == "Illustrative AI Governance Circular"
    assert detail.json()["document"]["filename"] == "circular.txt"
    assert len(detail.json()["sections"]) >= 1


def test_duplicate_content_does_not_create_another_document_version():
    content = (
        "Illustrative Cybersecurity Circular\n"
        "Central Bank of the UAE\n"
        "A regulated entity shall maintain documented security incident procedures.\n"
    )
    first = upload_text(content, "first.txt")
    second = upload_text(content, "renamed-copy.txt")
    assert first.status_code == 200
    assert second.status_code == 200
    assert first.json()["persistence"]["document_version_id"] == second.json()["persistence"]["document_version_id"]
    assert second.json()["persistence"]["duplicate"] is True
    assert client.get("/api/v1/documents").json()["total"] == 1


def test_document_repository_search_and_jurisdiction_filter():
    india = upload_text(
        "Illustrative RBI Circular\nReserve Bank of India\nA bank shall maintain model review evidence.\n",
        "india.txt",
    )
    uae = upload_text(
        "Illustrative CBUAE Guidance\nCentral Bank of the UAE\nA bank shall document incident reviews.\n",
        "uae.txt",
    )
    assert india.status_code == uae.status_code == 200
    india_docs = client.get("/api/v1/documents", params={"jurisdiction": "India"}).json()
    assert india_docs["total"] == 1
    search = client.get("/api/v1/documents", params={"q": "CBUAE"}).json()
    assert search["total"] == 1


def test_persisted_publication_appears_in_publication_feed_after_reload():
    response = upload_text(
        "Illustrative AI Governance Circular\nReserve Bank of India\nA regulated entity shall maintain an AI inventory.\n"
    )
    assert response.status_code == 200
    publications = client.get("/api/v1/publications").json()["items"]
    assert any(item["id"] == response.json()["publication"]["id"] for item in publications)
    overview = client.get("/api/v1/overview").json()
    assert overview["total_publications"] >= 6


def test_private_document_apis_are_disabled_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    response = client.post(
        "/api/v1/documents",
        files={"file": ("private.txt", b"An entity shall retain audit evidence.", "text/plain")},
    )
    assert response.status_code == 503
    assert "authentication" in response.json()["detail"].lower()

    listing = client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["access_enabled"] is False
    assert listing.json()["persistence_available"] is False
