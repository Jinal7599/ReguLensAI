from __future__ import annotations

from datetime import date, datetime, timezone
from uuid import uuid4

from sqlalchemy import (
    Boolean, Date, DateTime, Float, ForeignKey, Index, Integer, JSON,
    String, Text, UniqueConstraint,
)
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


def new_id() -> str:
    return str(uuid4())


def utc_now() -> datetime:
    return datetime.now(timezone.utc)


class Base(DeclarativeBase):
    pass


class RegulatoryAuthority(Base):
    __tablename__ = "regulatory_authorities"
    __table_args__ = (UniqueConstraint("name", "jurisdiction", name="uq_authority_name_jurisdiction"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    name: Mapped[str] = mapped_column(String(240), nullable=False)
    jurisdiction: Mapped[str] = mapped_column(String(120), nullable=False)
    region: Mapped[str | None] = mapped_column(String(120))
    website_url: Mapped[str | None] = mapped_column(String(1000))
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class RegulatoryInstrument(Base):
    __tablename__ = "regulatory_instruments"
    __table_args__ = (UniqueConstraint("authority_id", "canonical_key", name="uq_instrument_authority_key"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    authority_id: Mapped[str | None] = mapped_column(ForeignKey("regulatory_authorities.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(240))
    canonical_key: Mapped[str] = mapped_column(String(700), nullable=False)
    instrument_type: Mapped[str | None] = mapped_column(String(120))
    jurisdiction: Mapped[str] = mapped_column(String(120), nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class Publication(Base):
    __tablename__ = "publications"
    __table_args__ = (
        Index("ix_publications_jurisdiction_date", "jurisdiction", "publication_date"),
        Index("ix_publications_authority", "authority_id"),
    )

    id: Mapped[str] = mapped_column(String(80), primary_key=True)
    authority_id: Mapped[str | None] = mapped_column(ForeignKey("regulatory_authorities.id", ondelete="SET NULL"))
    instrument_id: Mapped[str | None] = mapped_column(ForeignKey("regulatory_instruments.id", ondelete="SET NULL"))
    title: Mapped[str] = mapped_column(String(500), nullable=False)
    reference_number: Mapped[str | None] = mapped_column(String(240))
    jurisdiction: Mapped[str] = mapped_column(String(120), nullable=False, default="Unknown")
    publication_date: Mapped[date | None] = mapped_column(Date)
    effective_date: Mapped[date | None] = mapped_column(Date)
    document_type: Mapped[str | None] = mapped_column(String(120))
    business_areas: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    source_url: Mapped[str | None] = mapped_column(String(2000))
    status: Mapped[str] = mapped_column(String(80), default="Awaiting review", nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class DocumentVersion(Base):
    __tablename__ = "document_versions"
    __table_args__ = (
        UniqueConstraint("sha256", name="uq_document_versions_sha256"),
        Index("ix_document_versions_publication", "publication_id"),
    )

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    filename: Mapped[str] = mapped_column(String(500), nullable=False)
    extension: Mapped[str] = mapped_column(String(20), nullable=False)
    mime_type: Mapped[str | None] = mapped_column(String(160))
    size_bytes: Mapped[int] = mapped_column(Integer, nullable=False)
    sha256: Mapped[str] = mapped_column(String(64), nullable=False)
    storage_uri: Mapped[str | None] = mapped_column(String(2000))
    extracted_text: Mapped[str] = mapped_column(Text, nullable=False, default="")
    extraction_method: Mapped[str] = mapped_column(String(120), nullable=False)
    extraction_model: Mapped[str | None] = mapped_column(String(160))
    extraction_status: Mapped[str] = mapped_column(String(40), nullable=False, default="completed")
    extraction_metadata: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    extraction_result: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, onupdate=utc_now, nullable=False)


class DocumentSection(Base):
    __tablename__ = "document_sections"
    __table_args__ = (UniqueConstraint("document_version_id", "ordinal", name="uq_document_section_ordinal"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    ordinal: Mapped[int] = mapped_column(Integer, nullable=False)
    source_reference: Mapped[str] = mapped_column(String(240), nullable=False)
    section_type: Mapped[str] = mapped_column(String(80), nullable=False, default="source_segment")
    heading: Mapped[str | None] = mapped_column(String(500))
    text: Mapped[str] = mapped_column(Text, nullable=False)


class Obligation(Base):
    __tablename__ = "obligations"
    __table_args__ = (Index("ix_obligations_document_version", "document_version_id"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    section_id: Mapped[str | None] = mapped_column(ForeignKey("document_sections.id", ondelete="SET NULL"))
    requirement: Mapped[str] = mapped_column(Text, nullable=False)
    classification: Mapped[str] = mapped_column(String(120), nullable=False)
    applies_to: Mapped[list] = mapped_column(JSON, default=list, nullable=False)
    deadline: Mapped[str | None] = mapped_column(String(240))
    source_reference: Mapped[str] = mapped_column(String(240), nullable=False)
    source_excerpt: Mapped[str] = mapped_column(Text, nullable=False)
    evidence_verified: Mapped[bool] = mapped_column(Boolean, default=False, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class DocumentRelationship(Base):
    __tablename__ = "document_relationships"
    __table_args__ = (UniqueConstraint("source_publication_id", "target_publication_id", "relation_type", name="uq_document_relationship"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    source_publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    target_publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    relation_type: Mapped[str] = mapped_column(String(80), nullable=False)
    confidence: Mapped[float | None] = mapped_column(Float)
    matching_method: Mapped[str | None] = mapped_column(String(120))
    review_status: Mapped[str] = mapped_column(String(40), default="pending", nullable=False)
    evidence: Mapped[dict] = mapped_column(JSON, default=dict, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)


class AnalysisJob(Base):
    __tablename__ = "analysis_jobs"
    __table_args__ = (Index("ix_analysis_jobs_status_created", "status", "created_at"),)

    id: Mapped[str] = mapped_column(String(36), primary_key=True, default=new_id)
    publication_id: Mapped[str] = mapped_column(ForeignKey("publications.id", ondelete="CASCADE"), nullable=False)
    document_version_id: Mapped[str] = mapped_column(ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False)
    job_type: Mapped[str] = mapped_column(String(80), nullable=False)
    status: Mapped[str] = mapped_column(String(40), default="completed", nullable=False)
    progress: Mapped[int] = mapped_column(Integer, default=100, nullable=False)
    attempts: Mapped[int] = mapped_column(Integer, default=1, nullable=False)
    error_message: Mapped[str | None] = mapped_column(Text)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=utc_now, nullable=False)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    completed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
