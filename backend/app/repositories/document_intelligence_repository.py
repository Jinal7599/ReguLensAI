from __future__ import annotations

from typing import Any

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.models import (
    DocumentSection, DocumentVersion, Obligation, RegulatoryClause, RegulatoryReference,
)


def persist_document_intelligence(
    session: Session,
    document_version_id: str,
    extraction: dict[str, Any],
) -> dict[str, int]:
    """Persist normalized clauses, obligation links and cross-references."""
    session.execute(delete(RegulatoryClause).where(RegulatoryClause.document_version_id == document_version_id))
    session.execute(delete(RegulatoryReference).where(RegulatoryReference.source_document_version_id == document_version_id))

    clauses = extraction.get("clauses", []) or []
    for ordinal, item in enumerate(clauses, start=1):
        text = str(item.get("text") or item.get("clause_text") or "").strip()
        if not text:
            continue
        session.add(RegulatoryClause(
            document_version_id=document_version_id,
            ordinal=ordinal,
            clause_number=str(item.get("clause_number") or "Not identified")[:120],
            heading=str(item.get("heading") or "")[:500] or None,
            clause_type=str(item.get("clause_type") or "regulatory_text")[:80],
            text=text,
            source_reference=str(item.get("source_reference") or "Unknown")[:240],
            evidence_verified=bool(item.get("evidence_verified", False)),
        ))

    session.flush()
    clause_rows = session.scalars(
        select(RegulatoryClause)
        .where(RegulatoryClause.document_version_id == document_version_id)
        .order_by(RegulatoryClause.ordinal)
    ).all()
    obligation_rows = session.scalars(
        select(Obligation).where(Obligation.document_version_id == document_version_id)
    ).all()

    for obligation in obligation_rows:
        candidates = [
            clause for clause in clause_rows
            if clause.source_reference == obligation.source_reference
            and obligation.source_excerpt
            and " ".join(obligation.source_excerpt.casefold().split())
            in " ".join(clause.text.casefold().split())
        ]
        if not candidates and obligation.requirement:
            candidates = [
                clause for clause in clause_rows
                if clause.source_reference == obligation.source_reference
                and " ".join(obligation.requirement.casefold().split())
                in " ".join(clause.text.casefold().split())
            ]
        if candidates:
            obligation.clause_id = candidates[0].id

        for item in extraction.get("obligations", []) or []:
            if (
                str(item.get("source_reference") or "") == obligation.source_reference
                and str(item.get("source_excerpt") or "").strip() == obligation.source_excerpt.strip()
            ):
                obligation.clause_number = str(item.get("clause_number") or "")[:120] or None
                obligation.obligation_type = str(item.get("obligation_type") or "")[:80] or None
                obligation.affected_entities = [
                    str(value) for value in item.get("affected_entities", []) if str(value).strip()
                ]
                obligation.departments = [
                    str(value) for value in item.get("departments", []) if str(value).strip()
                ]
                break

    references = extraction.get("references", []) or []
    for item in references:
        excerpt = str(item.get("source_excerpt") or "").strip()
        reference_number = str(item.get("reference_number") or "").strip()
        title = str(item.get("referenced_title") or "").strip()
        if not excerpt and not reference_number and not title:
            continue
        session.add(RegulatoryReference(
            source_document_version_id=document_version_id,
            referenced_title=title[:500] or None,
            reference_number=reference_number[:240] or None,
            relationship_type=str(item.get("relationship_type") or "references")[:80],
            source_reference=str(item.get("source_reference") or "Unknown")[:240],
            source_excerpt=excerpt,
            evidence_verified=bool(item.get("evidence_verified", False)),
        ))
    session.commit()
    return {
        "stored_clauses": len([
            item for item in clauses
            if str(item.get("text") or item.get("clause_text") or "").strip()
        ]),
        "stored_references": len([
            item for item in references
            if str(item.get("source_excerpt") or item.get("reference_number") or item.get("referenced_title") or "").strip()
        ]),
        "linked_obligations": sum(1 for item in obligation_rows if item.clause_id),
    }


def ensure_document_clauses(session: Session, document_version_id: str) -> list[RegulatoryClause]:
    """Load clauses, reconstructing a conservative legacy representation when needed."""
    clauses = session.scalars(
        select(RegulatoryClause)
        .where(RegulatoryClause.document_version_id == document_version_id)
        .order_by(RegulatoryClause.ordinal)
    ).all()
    if clauses:
        return clauses

    version = session.get(DocumentVersion, document_version_id)
    if version is None:
        return []
    extraction = (version.extraction_result or {}).get("extraction", {})
    extracted_clauses = extraction.get("clauses", []) or []
    reconstructed: list[dict[str, Any]] = []

    if extracted_clauses:
        reconstructed = extracted_clauses
    else:
        from app.services.document_ingestion import TextSegment
        from app.services.document_intelligence import fallback_clauses

        sections = session.scalars(
            select(DocumentSection)
            .where(DocumentSection.document_version_id == document_version_id)
            .order_by(DocumentSection.ordinal)
        ).all()
        segments = [
            TextSegment(reference=section.source_reference, text=section.text)
            for section in sections
        ]
        reconstructed = fallback_clauses(segments)

        # Older saved records only had obligation-level extraction. Preserve those
        # explicit candidate clauses even when sentence segmentation did not retain them.
        for obligation in extraction.get("obligations", []) or []:
            requirement = str(obligation.get("source_excerpt") or obligation.get("requirement") or "").strip()
            if not requirement:
                continue
            if any(requirement.casefold() in str(item.get("text") or "").casefold() for item in reconstructed):
                continue
            reconstructed.append({
                "clause_number": str(obligation.get("clause_number") or "Not identified"),
                "heading": "",
                "clause_type": "obligation",
                "text": requirement,
                "source_reference": str(obligation.get("source_reference") or "Unknown"),
                "evidence_verified": bool(obligation.get("evidence_verified", False)),
            })

    for ordinal, item in enumerate(reconstructed[:500], start=1):
        text = str(item.get("text") or item.get("clause_text") or "").strip()
        if not text:
            continue
        session.add(RegulatoryClause(
            document_version_id=document_version_id,
            ordinal=ordinal,
            clause_number=str(item.get("clause_number") or "Not identified")[:120],
            heading=str(item.get("heading") or "")[:500] or None,
            clause_type=str(item.get("clause_type") or "regulatory_text")[:80],
            text=text,
            source_reference=str(item.get("source_reference") or "Unknown")[:240],
            evidence_verified=bool(item.get("evidence_verified", False)),
        ))
    session.commit()
    return session.scalars(
        select(RegulatoryClause)
        .where(RegulatoryClause.document_version_id == document_version_id)
        .order_by(RegulatoryClause.ordinal)
    ).all()
