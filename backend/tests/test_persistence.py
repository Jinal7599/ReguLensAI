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
    assert persistence["stored_clauses"] >= 1
    assert payload["comparison"]["status"] == "no_history"

    listing = client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["total"] == 1
    document_id = listing.json()["items"][0]["document_version_id"]

    detail = client.get(f"/api/v1/documents/{document_id}")
    assert detail.status_code == 200
    assert detail.json()["publication"]["title"] == "Illustrative AI Governance Circular"
    assert detail.json()["document"]["filename"] == "circular.txt"
    assert len(detail.json()["sections"]) >= 1
    assert len(detail.json()["extraction"]["clauses"]) >= 1


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


def test_duplicate_upload_retries_comparison_after_historical_document_is_added(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    amendment_text = (
        "Amendment to Digital Lending Directions\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2026-27/950\n"
        "Published on 31/10/2026\n"
        "This circular amends Circular No: RBI/2025-26/950.\n"
        "Clause 4.2: Regulated entities shall conduct quarterly reviews of lending models and maintain documented review evidence.\n"
    )
    first_upload = upload_text(amendment_text, "digital-lending-amendment.txt")
    assert first_upload.status_code == 200
    assert first_upload.json()["comparison"]["status"] == "no_history"

    historical = upload_text(
        "Illustrative Digital Lending Directions\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2025-26/950\n"
        "Published on 10/01/2025\n"
        "Clause 4.2: Regulated entities shall review their lending models periodically.\n",
        "digital-lending-older.txt",
    )
    assert historical.status_code == 200

    retry = upload_text(amendment_text, "digital-lending-amendment.txt")
    assert retry.status_code == 200
    assert retry.json()["persistence"]["duplicate"] is True
    comparison = retry.json()["comparison"]
    assert comparison["status"] == "compared"
    assert comparison["documents_matched"] == 1
    assert comparison["finding_count"] >= 1
    assert comparison["comparisons"][0]["relationship_type"] == "amends"
    assert any(
        item["classification"] == "Modified obligation"
        for item in comparison["comparisons"][0]["findings"]
    )


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


def test_private_document_apis_require_authentication_in_production(monkeypatch):
    monkeypatch.setenv("APP_ENV", "production")
    response = client.post(
        "/api/v1/documents",
        files={"file": ("private.txt", b"An entity shall retain audit evidence.", "text/plain")},
    )
    assert response.status_code == 401
    assert "authentication" in response.json()["detail"].lower()

    listing = client.get("/api/v1/documents")
    assert listing.status_code == 200
    assert listing.json()["access_enabled"] is False
    assert listing.json()["persistence_available"] is False



def test_new_document_compares_against_all_saved_historical_documents(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    historical = upload_text(
        "Illustrative Digital Lending Directions\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2025-26/101\n"
        "Published on 10/01/2025\n"
        "Clause 4.2: Regulated entities shall review their lending models periodically.\n",
        "digital-lending-2025.txt",
    )
    assert historical.status_code == 200
    assert historical.json()["persistence"]["stored_clauses"] >= 1

    updated = upload_text(
        "Amendment to Digital Lending Directions\n"
        "Reserve Bank of India\n"
        "Circular No: RBI/2026-27/212\n"
        "Published on 20/10/2026\n"
        "This circular amends Circular No: RBI/2025-26/101.\n"
        "Clause 4.2: Regulated entities shall conduct quarterly reviews of lending models and maintain documented evidence of the review.\n",
        "digital-lending-amendment-2026.txt",
    )
    assert updated.status_code == 200
    payload = updated.json()
    assert payload["persistence"]["stored_clauses"] >= 1
    comparison = payload["comparison"]

    assert comparison["status"] == "compared"
    assert comparison["documents_considered"] == 1
    assert comparison["documents_matched"] == 1
    assert comparison["finding_count"] >= 1, comparison
    item = comparison["comparisons"][0]
    assert item["historical_title"] == "Illustrative Digital Lending Directions"
    assert item["relationship_type"] == "amends"
    assert item["matching_method"] == "explicit_reference"
    assert item["findings"]
    assert any(finding["classification"] == "Modified obligation" for finding in item["findings"])
    assert any(finding["previous_source_reference"] and finding["updated_source_reference"] for finding in item["findings"])

    document_version_id = payload["persistence"]["document_version_id"]
    reopened = client.get(f"/api/v1/documents/{document_version_id}")
    assert reopened.status_code == 200
    assert reopened.json()["comparison"]["documents_matched"] == 1
    assert reopened.json()["comparison"]["finding_count"] >= 1

    comparisons_endpoint = client.get(f"/api/v1/documents/{document_version_id}/comparisons")
    assert comparisons_endpoint.status_code == 200
    assert comparisons_endpoint.json()["comparisons"][0]["findings"]


def test_repository_does_not_mark_missing_old_clauses_as_withdrawn_without_explicit_repeal(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    historical = upload_text(
        "Illustrative Operational Resilience Guidance\n"
        "Central Bank of the UAE\n"
        "Circular No: CBUAE/2025/55\n"
        "Clause 3.1: Regulated entities shall maintain incident response plans.\n"
        "Clause 3.2: Regulated entities shall test recovery procedures annually.\n",
        "resilience-2025.txt",
    )
    assert historical.status_code == 200

    updated = upload_text(
        "Amendment to Operational Resilience Guidance\n"
        "Central Bank of the UAE\n"
        "Circular No: CBUAE/2026/88\n"
        "This circular amends Circular No: CBUAE/2025/55.\n"
        "Clause 3.1: Regulated entities shall maintain tested incident response plans.\n",
        "resilience-amendment-2026.txt",
    )
    assert updated.status_code == 200
    findings = updated.json()["comparison"]["comparisons"][0]["findings"]
    assert all(item["classification"] != "Withdrawn / superseded" for item in findings)
