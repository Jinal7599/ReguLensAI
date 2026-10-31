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


def test_text_document_upload_extracts_obligation_with_source_evidence(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    content = (
        "Illustrative AI Governance Circular\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2026-27/014\n"
        "Published on 20/10/2026\n"
        "This circular applies to regulated entities in India.\n"
        "Regulated entities shall maintain a documented inventory of AI systems used in credit decisions. "
        "The inventory must be reviewed at least once every year.\n"
        "These requirements are effective from 01/04/2027.\n"
    )
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("rbi-ai-circular.txt", content, "text/plain")},
    )

    assert response.status_code == 200
    payload = response.json()
    assert payload["publication"]["title"] == "Illustrative AI Governance Circular"
    assert payload["publication"]["country"] == "India"
    assert payload["publication"]["status"] == "Awaiting review"
    assert payload["extraction"]["method"] == "Rule-based fallback"
    assert payload["extraction"]["obligation_count"] >= 1
    first = payload["extraction"]["obligations"][0]
    assert first["source_reference"].startswith("TXT line")
    assert first["evidence_verified"] is True
    assert "shall" in first["source_excerpt"].lower()


def test_document_upload_rejects_unsupported_file_type():
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("policy.csv", "a,b\n1,2", "text/csv")},
    )
    assert response.status_code == 415


def test_document_upload_rejects_files_over_10mb():
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("large.txt", b"x" * (10 * 1024 * 1024 + 1), "text/plain")},
    )
    assert response.status_code == 413


def test_scanned_or_non_text_pdf_returns_actionable_error():
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("empty-scan.pdf", b"not a valid PDF", "application/pdf")},
    )
    assert response.status_code == 422
