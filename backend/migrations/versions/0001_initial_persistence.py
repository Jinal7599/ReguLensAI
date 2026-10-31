"""Initial PostgreSQL persistence foundation.

Revision ID: 0001_initial_persistence
Revises:
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0001_initial_persistence"
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_authorities",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("name", sa.String(240), nullable=False),
        sa.Column("jurisdiction", sa.String(120), nullable=False),
        sa.Column("region", sa.String(120)),
        sa.Column("website_url", sa.String(1000)),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("name", "jurisdiction", name="uq_authority_name_jurisdiction"),
    )
    op.create_table(
        "regulatory_instruments",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("authority_id", sa.String(36), sa.ForeignKey("regulatory_authorities.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("reference_number", sa.String(240)),
        sa.Column("canonical_key", sa.String(700), nullable=False),
        sa.Column("instrument_type", sa.String(120)),
        sa.Column("jurisdiction", sa.String(120), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("authority_id", "canonical_key", name="uq_instrument_authority_key"),
    )
    op.create_table(
        "publications",
        sa.Column("id", sa.String(80), primary_key=True),
        sa.Column("authority_id", sa.String(36), sa.ForeignKey("regulatory_authorities.id", ondelete="SET NULL")),
        sa.Column("instrument_id", sa.String(36), sa.ForeignKey("regulatory_instruments.id", ondelete="SET NULL")),
        sa.Column("title", sa.String(500), nullable=False),
        sa.Column("reference_number", sa.String(240)),
        sa.Column("jurisdiction", sa.String(120), nullable=False),
        sa.Column("publication_date", sa.Date()),
        sa.Column("effective_date", sa.Date()),
        sa.Column("document_type", sa.String(120)),
        sa.Column("business_areas", sa.JSON(), nullable=False),
        sa.Column("source_url", sa.String(2000)),
        sa.Column("status", sa.String(80), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_publications_jurisdiction_date", "publications", ["jurisdiction", "publication_date"])
    op.create_index("ix_publications_authority", "publications", ["authority_id"])
    op.create_table(
        "document_versions",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("publication_id", sa.String(80), sa.ForeignKey("publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("filename", sa.String(500), nullable=False),
        sa.Column("extension", sa.String(20), nullable=False),
        sa.Column("mime_type", sa.String(160)),
        sa.Column("size_bytes", sa.Integer(), nullable=False),
        sa.Column("sha256", sa.String(64), nullable=False),
        sa.Column("storage_uri", sa.String(2000)),
        sa.Column("extracted_text", sa.Text(), nullable=False),
        sa.Column("extraction_method", sa.String(120), nullable=False),
        sa.Column("extraction_model", sa.String(160)),
        sa.Column("extraction_status", sa.String(40), nullable=False),
        sa.Column("extraction_metadata", sa.JSON(), nullable=False),
        sa.Column("extraction_result", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("sha256", name="uq_document_versions_sha256"),
    )
    op.create_index("ix_document_versions_publication", "document_versions", ["publication_id"])
    op.create_table(
        "document_sections",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("source_reference", sa.String(240), nullable=False),
        sa.Column("section_type", sa.String(80), nullable=False),
        sa.Column("heading", sa.String(500)),
        sa.Column("text", sa.Text(), nullable=False),
        sa.UniqueConstraint("document_version_id", "ordinal", name="uq_document_section_ordinal"),
    )
    op.create_table(
        "obligations",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("section_id", sa.String(36), sa.ForeignKey("document_sections.id", ondelete="SET NULL")),
        sa.Column("requirement", sa.Text(), nullable=False),
        sa.Column("classification", sa.String(120), nullable=False),
        sa.Column("applies_to", sa.JSON(), nullable=False),
        sa.Column("deadline", sa.String(240)),
        sa.Column("source_reference", sa.String(240), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column("evidence_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_obligations_document_version", "obligations", ["document_version_id"])
    op.create_table(
        "document_relationships",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_publication_id", sa.String(80), sa.ForeignKey("publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("target_publication_id", sa.String(80), sa.ForeignKey("publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relation_type", sa.String(80), nullable=False),
        sa.Column("confidence", sa.Float()),
        sa.Column("matching_method", sa.String(120)),
        sa.Column("review_status", sa.String(40), nullable=False),
        sa.Column("evidence", sa.JSON(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("source_publication_id", "target_publication_id", "relation_type", name="uq_document_relationship"),
    )
    op.create_table(
        "analysis_jobs",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("publication_id", sa.String(80), sa.ForeignKey("publications.id", ondelete="CASCADE"), nullable=False),
        sa.Column("document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("job_type", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("progress", sa.Integer(), nullable=False),
        sa.Column("attempts", sa.Integer(), nullable=False),
        sa.Column("error_message", sa.Text()),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True)),
        sa.Column("completed_at", sa.DateTime(timezone=True)),
    )
    op.create_index("ix_analysis_jobs_status_created", "analysis_jobs", ["status", "created_at"])


def downgrade() -> None:
    op.drop_index("ix_analysis_jobs_status_created", table_name="analysis_jobs")
    op.drop_table("analysis_jobs")
    op.drop_table("document_relationships")
    op.drop_index("ix_obligations_document_version", table_name="obligations")
    op.drop_table("obligations")
    op.drop_table("document_sections")
    op.drop_index("ix_document_versions_publication", table_name="document_versions")
    op.drop_table("document_versions")
    op.drop_index("ix_publications_authority", table_name="publications")
    op.drop_index("ix_publications_jurisdiction_date", table_name="publications")
    op.drop_table("publications")
    op.drop_table("regulatory_instruments")
    op.drop_table("regulatory_authorities")
