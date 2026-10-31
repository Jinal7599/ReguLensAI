from __future__ import annotations

from collections import Counter
from fastapi import APIRouter, File, HTTPException, Query, UploadFile
from starlette.concurrency import run_in_threadpool

from app.data.demo_data import CHANGES, PUBLICATIONS, SOURCES
from app.services.document_ingestion import (
    MAX_UPLOAD_BYTES,
    DocumentIngestionError,
    analyze_document,
)

router = APIRouter(prefix="/api/v1", tags=["Regulatory intelligence"])


@router.get("/health")
def health() -> dict[str, str]:
    return {"status": "ok", "service": "regulens-api", "version": "1.0.0"}


@router.get("/overview")
def overview() -> dict:
    status_counts = Counter(item["status"] for item in PUBLICATIONS)
    country_counts = Counter(item["country"] for item in PUBLICATIONS)
    return {
        "total_publications": len(PUBLICATIONS),
        "new_or_unreviewed": sum(item["status"] in {"New", "Awaiting review", "Relationship unresolved"} for item in PUBLICATIONS),
        "awaiting_review": status_counts["Awaiting review"],
        "regions_represented": len(country_counts),
        "coverage": [{"country": country, "count": count} for country, count in sorted(country_counts.items())],
        "recent_publications": PUBLICATIONS[:5],
    }


@router.get("/publications")
def publications(
    q: str = Query(default="", description="Search title, authority, ID or business area"),
    country: str = Query(default=""),
    status: str = Query(default=""),
) -> dict:
    items = PUBLICATIONS
    if q.strip():
        term = q.strip().casefold()
        items = [item for item in items if term in " ".join(str(value) for value in item.values()).casefold()]
    if country:
        items = [item for item in items if item["country"] == country]
    if status:
        items = [item for item in items if item["status"] == status]
    return {"items": items, "total": len(items)}


@router.get("/changes")
def changes() -> dict:
    return {"items": CHANGES, "total": len(CHANGES)}


@router.get("/sources")
def sources() -> dict:
    return {"items": SOURCES, "total": len(SOURCES)}


@router.post("/documents/analyze")
async def analyze_uploaded_document(file: UploadFile = File(...)) -> dict:
    filename = file.filename or "uploaded-document"
    extension = filename.rsplit(".", 1)[-1].lower() if "." in filename else ""
    if f".{extension}" not in {".pdf", ".docx", ".txt"}:
        raise HTTPException(status_code=415, detail="Supported formats: PDF, DOCX and TXT.")

    content = await file.read(MAX_UPLOAD_BYTES + 1)
    if len(content) > MAX_UPLOAD_BYTES:
        raise HTTPException(status_code=413, detail="File exceeds the 10 MB upload limit.")

    try:
        return await run_in_threadpool(analyze_document, filename, content)
    except DocumentIngestionError as exc:
        raise HTTPException(status_code=422, detail=str(exc)) from exc
    except Exception as exc:
        raise HTTPException(status_code=500, detail="Document analysis failed unexpectedly.") from exc
