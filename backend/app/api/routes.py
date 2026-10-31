from __future__ import annotations

import hashlib
from copy import deepcopy
from typing import Any

from fastapi import APIRouter, Depends, File, HTTPException, Query, UploadFile
from sqlalchemy import select
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from starlette.concurrency import run_in_threadpool

from app.data.demo_data import CHANGES, PUBLICATIONS, SOURCES
from app.core.config import gemini_configuration
from app.db.models import Publication, RegulatoryAuthority
from app.db.session import get_db, get_optional_db, private_document_access_enabled, resolve_database_url
from app.repositories.document_repository import (
    duplicate_persistence_result,
    find_document_by_hash,
    get_document_detail,
    list_documents,
    persist_analysis,
    publication_to_dict,
)
from app.services.document_ingestion import (
    MAX_UPLOAD_BYTES,
    DocumentIngestionError,
    analyze_document,
)

router = APIRouter(prefix="/api/v1", tags=["Regulatory intelligence"])


def _database_publications(session: Session | None) -> list[dict[str, Any]]:
    if session is None:
        return []
    rows = session.execute(
        select(Publication, RegulatoryAuthority)
        .outerjoin(RegulatoryAuthority, RegulatoryAuthority.id == Publication.authority_id)
        .order_by(Publication.created_at.desc())
    ).all()
    return [publication_to_dict(publication, authority.name if authority else None) for publication, authority in rows]


@router.get("/health")
def health() -> dict[str, Any]:
    database_url = resolve_database_url()
    return {
        "status": "ok",
        "service": "regulens-api",
        "version": "1.1.0",
        "persistence_configured": bool(database_url),
        "document_data_access_enabled": private_document_access_enabled(),
        "database_backend": "postgresql" if database_url and database_url.startswith("postgresql") else ("sqlite" if database_url else None),
    }


@router.get("/diagnostics/gemini")
def gemini_diagnostics() -> dict:
    """Report Gemini configuration state without exposing the API key."""
    return gemini_configuration()


@router.get("/diagnostics/storage")
def storage_diagnostics() -> dict[str, Any]:
    database_url = resolve_database_url()
    configured = bool(database_url)
    backend = "postgresql" if database_url and database_url.startswith("postgresql") else ("sqlite" if database_url else "missing")
    return {
        "configured": configured,
        "backend": backend,
        "durable_storage_expected": backend == "postgresql",
        "document_data_access_enabled": private_document_access_enabled(),
        "message": (
            "Database is configured, but document APIs remain disabled on this public deployment until authentication is implemented."
            if configured and not private_document_access_enabled()
            else ("Database URL detected. Verify connectivity and migrations before enabling private document APIs."
                  if configured else "DATABASE_URL is missing. Set it to a PostgreSQL connection string in production.")
        ),
    }


@router.get("/overview")
def overview(session: Session | None = Depends(get_optional_db)) -> dict:
    publications = _database_publications(session) + PUBLICATIONS
    status_counts: dict[str, int] = {}
    country_counts: dict[str, int] = {}
    for item in publications:
        status_counts[item["status"]] = status_counts.get(item["status"], 0) + 1
        country_counts[item["country"]] = country_counts.get(item["country"], 0) + 1
    return {
        "total_publications": len(publications),
        "new_or_unreviewed": sum(item["status"] in {"New", "Awaiting review", "Relationship unresolved"} for item in publications),
        "awaiting_review": status_counts.get("Awaiting review", 0),
        "regions_represented": len(country_counts),
        "coverage": [{"country": country, "count": count} for country, count in sorted(country_counts.items())],
        "recent_publications": publications[:5],
    }


@router.get("/publications")
def publications(
    q: str = Query(default="", description="Search title, authority, ID or business area"),
    country: str = Query(default=""),
    status: str = Query(default=""),
    session: Session | None = Depends(get_optional_db),
) -> dict:
    items = _database_publications(session) + PUBLICATIONS
    if q.strip():
        term = q.strip().casefold()
        items = [item for item in items if term in " ".join(str(value) for value in item.values()).casefold()]
    if country:
        items = [item for item in items if item["country"] == country]
    if status:
        items = [item for item in items if item["status"] == status]
    return {"items": items, "total": len(items)}


@router.get("/documents")
def documents(
    q: str = Query(default=""),
    jurisdiction: str = Query(default=""),
    limit: int = Query(default=50, ge=1, le=200),
    offset: int = Query(default=0, ge=0),
    session: Session | None = Depends(get_optional_db),
) -> dict:
    if session is None:
        return {
            "items": [],
            "total": 0,
            "limit": limit,
            "offset": offset,
            "persistence_available": False,
            "access_enabled": False,
            "message": "Saved document access is disabled on this public deployment until authentication is implemented.",
        }
    result = list_documents(session, q=q, jurisdiction=jurisdiction, limit=limit, offset=offset)
    result["persistence_available"] = True
    return result


@router.get("/documents/{document_version_id}")
def document_detail(document_version_id: str, session: Session = Depends(get_db)) -> dict:
    result = get_document_detail(session, document_version_id)
    if result is None:
        raise HTTPException(status_code=404, detail="Document version was not found.")
    return result


@router.get("/changes")
def changes() -> dict:
    return {"items": CHANGES, "total": len(CHANGES)}


@router.get("/sources")
def sources() -> dict:
    return {"items": SOURCES, "total": len(SOURCES)}


@router.post("/documents")
@router.post("/documents/analyze", include_in_schema=False)
async def analyze_uploaded_document(
    file: UploadFile = File(...),
    session: Session = Depends(get_db),
) -> dict:
    filename = file.filename or "uploaded-document"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{extension}" not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, DOCX and TXT.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB upload limit.")

    checksum = hashlib.sha256(content).hexdigest()
    existing = find_document_by_hash(session, checksum)
    if existing:
        response = deepcopy(existing.extraction_result or {})
        response["persistence"] = duplicate_persistence_result(existing)
        response["persistence"]["original_file_stored"] = bool(existing.storage_uri)
        return response

    try:
        result = await run_in_threadpool(analyze_document, filename, content)
        persistence_context = result.pop("_persistence", {})
        persistence = persist_analysis(
            session,
            analysis=result,
            extracted_text=str(persistence_context.get("extracted_text") or ""),
            source_sections=persistence_context.get("source_sections") or [],
            mime_type=file.content_type,
        )
        persistence["original_file_stored"] = False
        result["persistence"] = persistence
        return result
    except DocumentIngestionError as exc:
        session.rollback()
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except IntegrityError:
        session.rollback()
        existing = find_document_by_hash(session, checksum)
        if existing:
            response = deepcopy(existing.extraction_result or {})
            response["persistence"] = duplicate_persistence_result(existing)
            response["persistence"]["original_file_stored"] = bool(existing.storage_uri)
            return response
        raise HTTPException(status_code=409, detail="A document with this content already exists; retry the request.")
    except Exception as exc:
        session.rollback()
        raise HTTPException(status_code=500, detail="Document analysis or persistence failed unexpectedly.") from exc
