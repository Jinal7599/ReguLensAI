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


def test_prohibition_language_is_classified_correctly(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    content = (
        "Illustrative Banking Circular\n"
        "A regulated entity must not disclose customer credentials to unauthorized persons.\n"
    )
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": ("prohibition.txt", content, "text/plain")},
    )
    assert response.status_code == 200
    assert response.json()["extraction"]["obligations"][0]["classification"] == "Prohibition"


def test_local_env_file_is_loaded_without_overriding_process_environment(tmp_path, monkeypatch):
    from app.core.config import load_local_environment

    project_root = tmp_path / "project"
    backend_root = project_root / "backend"
    backend_root.mkdir(parents=True)
    (project_root / ".env").write_text(
        "REGULENS_TEST_GEMINI_KEY=from-dotenv\n",
        encoding="utf-8",
    )
    monkeypatch.delenv("REGULENS_TEST_GEMINI_KEY", raising=False)
    load_local_environment(project_root=project_root, backend_root=backend_root)
    assert __import__("os").environ["REGULENS_TEST_GEMINI_KEY"] == "from-dotenv"


def test_explicit_gemini_environment_key_selects_gemini_path(monkeypatch):
    import app.services.document_ingestion as ingestion

    monkeypatch.setenv("GEMINI_API_KEY", "unit-test-key")
    monkeypatch.setattr(
        ingestion,
        "_run_gemini",
        lambda segments, filename: {
            "model": "test-model",
            "payload": {
                "document_metadata": {
                    "title": "Synthetic AI Circular",
                    "authority": "Test Regulator",
                    "jurisdiction": "India",
                    "publication_date": "Not identified",
                    "effective_date": "Not identified",
                    "reference_number": "Not identified",
                    "document_type": "Circular",
                    "business_area": "AI governance",
                },
                "summary": "Test Gemini summary.",
                "obligations": [{
                    "requirement": "A regulated entity shall maintain a model inventory.",
                    "classification": "Mandatory requirement",
                    "applies_to": ["Banking"],
                    "deadline": "Not identified",
                    "source_reference": "TXT line 2",
                    "source_excerpt": "A regulated entity shall maintain a model inventory.",
                }],
            },
        },
    )
    response = client.post(
        "/api/v1/documents/analyze",
        files={"file": (
            "gemini-test.txt",
            "Synthetic AI Circular\nA regulated entity shall maintain a model inventory.",
            "text/plain",
        )},
    )
    assert response.status_code == 200
    assert response.json()["extraction"]["method"] == "Gemini structured extraction"
    assert response.json()["extraction"]["gemini_status"] == "used"
    assert response.json()["extraction"]["model"] == "test-model"


def test_gemini_diagnostics_does_not_expose_secret(monkeypatch):
    monkeypatch.setenv("GEMINI_API_KEY", "never-return-this-secret")
    response = client.get("/api/v1/diagnostics/gemini")
    assert response.status_code == 200
    payload = response.json()
    assert payload["configured"] is True
    assert payload["key_source"] == "process environment"
    assert "never-return-this-secret" not in response.text


def test_dotenv_value_replaces_blank_process_environment_variable(tmp_path, monkeypatch):
    from app.core.config import load_local_environment

    project_root = tmp_path / "project"
    backend_root = project_root / "backend"
    backend_root.mkdir(parents=True)
    (project_root / ".env").write_text("GEMINI_API_KEY=test-from-file\n", encoding="utf-8")
    monkeypatch.setenv("GEMINI_API_KEY", "")
    load_local_environment(project_root=project_root, backend_root=backend_root)
    assert __import__("os").environ["GEMINI_API_KEY"] == "test-from-file"


def test_gemini_diagnostics_reports_missing_key(monkeypatch):
    monkeypatch.delenv("GEMINI_API_KEY", raising=False)
    response = client.get("/api/v1/diagnostics/gemini")
    assert response.status_code == 200
    assert response.json()["configured"] is False
    assert response.json()["key_source"] == "missing"
