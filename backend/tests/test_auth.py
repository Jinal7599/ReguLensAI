from __future__ import annotations

import uuid

from fastapi.testclient import TestClient
from sqlalchemy.orm import Session

from app.api import auth_routes
from app.db.models import DocumentVersion, Publication, User
from app.db.session import get_session_factory
from app.main import app
from app.repositories.document_repository import find_document_by_hash, list_documents
from app.services.repository_comparison import get_document_comparison_summary, run_repository_comparison
from app.services.auth import create_session_token

client = TestClient(app, base_url="https://testserver")


def _seed_user_and_document(session: Session, email: str, google_sub: str, checksum: str) -> tuple[User, str]:
    user = User(google_sub=google_sub, email=email, display_name=email.split("@")[0])
    publication = Publication(
        id=f"PUB-{uuid.uuid4().hex[:12]}",
        title=f"Private document for {email}",
        jurisdiction="India",
        status="Awaiting review",
    )
    session.add_all([user, publication])
    session.flush()
    version = DocumentVersion(
        owner_user_id=user.id,
        publication_id=publication.id,
        filename="private.txt",
        extension="txt",
        size_bytes=8,
        sha256=checksum,
        extraction_method="test",
        extraction_result={},
        extracted_text="private",
    )
    session.add(version)
    session.commit()
    return user, version.id


def test_production_private_document_routes_require_google_session(monkeypatch):
    client.cookies.clear()
    monkeypatch.setenv("APP_ENV", "production")
    response = client.get("/api/v1/documents")
    assert response.status_code == 401
    assert response.json()["detail"] == "Sign in with Google to access your documents."


def test_google_login_creates_secure_http_only_session_cookie(monkeypatch):
    client.cookies.clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("GOOGLE_CLIENT_ID", "test-client-id")
    monkeypatch.setenv("SESSION_SECRET", "test-secret-that-is-at-least-32-characters-long")
    monkeypatch.setenv("ALLOWED_ORIGINS", "https://frontend.example")
    nonce_response = client.post(
        "/api/v1/auth/nonce",
        headers={"Origin": "https://frontend.example", "X-ReguLens-Request": "browser"},
    )
    assert nonce_response.status_code == 200
    expected_nonce = nonce_response.json()["nonce"]
    monkeypatch.setattr(auth_routes, "verify_google_credential", lambda credential: {
        "sub": "google-sub-123", "email": "analyst@example.com", "email_verified": True,
        "name": "Regulatory Analyst", "picture": "https://example.com/avatar.png",
        "nonce": expected_nonce,
    })

    response = client.post(
        "/api/v1/auth/google",
        json={"credential": "a-valid-looking-google-id-token-credential"},
        headers={"Origin": "https://frontend.example", "X-ReguLens-Request": "browser"},
    )
    assert response.status_code == 200
    assert response.json()["user"]["email"] == "analyst@example.com"
    cookie = " ".join(response.headers.get_list("set-cookie"))
    session_cookie = next(value for value in response.headers.get_list("set-cookie") if value.startswith("regulens_session="))
    assert "HttpOnly" in session_cookie
    assert "Secure" in session_cookie
    assert "samesite=none" in session_cookie.lower()

    me = client.get("/api/v1/auth/me")
    assert me.status_code == 200
    assert me.json()["user"]["id"]
    client.cookies.clear()


def test_production_upload_requires_authentication(monkeypatch):
    client.cookies.clear()
    monkeypatch.setenv("APP_ENV", "production")
    response = client.post(
        "/api/v1/documents",
        files={"file": ("private.txt", "Confidential policy text.", "text/plain")},
    )
    assert response.status_code == 401


def test_document_queries_and_hash_deduplication_are_user_scoped():
    factory = get_session_factory()
    assert factory is not None
    with factory() as session:
        first_user, first_doc_id = _seed_user_and_document(
            session, "first@example.com", "google-sub-first", "same-checksum"
        )
        second_user, second_doc_id = _seed_user_and_document(
            session, "second@example.com", "google-sub-second", "same-checksum"
        )

        first_list = list_documents(session, owner_user_id=first_user.id)
        second_list = list_documents(session, owner_user_id=second_user.id)
        assert first_list["total"] == 1
        assert second_list["total"] == 1
        assert first_list["items"][0]["document_version_id"] == first_doc_id
        assert second_list["items"][0]["document_version_id"] == second_doc_id
        assert find_document_by_hash(session, "same-checksum", first_user.id).id == first_doc_id
        assert find_document_by_hash(session, "same-checksum", second_user.id).id == second_doc_id
        assert get_document_comparison_summary(session, first_doc_id, second_user.id)["status"] == "not_found"
        assert run_repository_comparison(session, first_doc_id, second_user.id)["status"] == "not_found"


def test_another_users_document_is_not_found(monkeypatch):
    client.cookies.clear()
    monkeypatch.setenv("APP_ENV", "production")
    monkeypatch.setenv("SESSION_SECRET", "test-secret-that-is-at-least-32-characters-long")
    factory = get_session_factory()
    assert factory is not None
    with factory() as session:
        first_user, _ = _seed_user_and_document(
            session, "owner@example.com", "owner-google-sub", "owner-checksum"
        )
        other_user, other_doc_id = _seed_user_and_document(
            session, "other@example.com", "other-google-sub", "other-checksum"
        )
        assert first_user.id != other_user.id
        token = create_session_token(first_user.id)
    client.cookies.set("regulens_session", token, domain="testserver", path="/")
    response = client.get(f"/api/v1/documents/{other_doc_id}")
    assert response.status_code == 404
    client.cookies.clear()
