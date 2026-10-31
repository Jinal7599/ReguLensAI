"""Persist structured clauses, regulatory references and historical comparisons.

Revision ID: 0002_document_intelligence_comparison
Revises: 0001_initial_persistence
Create Date: 2026-10-31
"""
from alembic import op
import sqlalchemy as sa

revision = "0002_document_intelligence_comparison"
down_revision = "0001_initial_persistence"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "regulatory_clauses",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("ordinal", sa.Integer(), nullable=False),
        sa.Column("clause_number", sa.String(120)),
        sa.Column("heading", sa.String(500)),
        sa.Column("clause_type", sa.String(80), nullable=False),
        sa.Column("text", sa.Text(), nullable=False),
        sa.Column("source_reference", sa.String(240), nullable=False),
        sa.Column("evidence_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("document_version_id", "ordinal", name="uq_regulatory_clause_ordinal"),
    )
    op.create_index("ix_regulatory_clauses_document", "regulatory_clauses", ["document_version_id"])

    op.add_column("obligations", sa.Column("clause_id", sa.String(36), nullable=True))
    op.add_column("obligations", sa.Column("clause_number", sa.String(120), nullable=True))
    op.add_column("obligations", sa.Column("obligation_type", sa.String(80), nullable=True))
    op.add_column("obligations", sa.Column("affected_entities", sa.JSON(), nullable=True))
    op.add_column("obligations", sa.Column("departments", sa.JSON(), nullable=True))
    op.create_table(
        "regulatory_references",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("source_document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("referenced_title", sa.String(500)),
        sa.Column("reference_number", sa.String(240)),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column("source_reference", sa.String(240), nullable=False),
        sa.Column("source_excerpt", sa.Text(), nullable=False),
        sa.Column("evidence_verified", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_regulatory_references_document", "regulatory_references", ["source_document_version_id"])

    op.create_table(
        "document_comparisons",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("new_document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("historical_document_version_id", sa.String(36), sa.ForeignKey("document_versions.id", ondelete="CASCADE"), nullable=False),
        sa.Column("relationship_type", sa.String(80), nullable=False),
        sa.Column("match_confidence", sa.Float(), nullable=False),
        sa.Column("matching_method", sa.String(120), nullable=False),
        sa.Column("match_evidence", sa.JSON(), nullable=False),
        sa.Column("analysis_method", sa.String(80), nullable=False),
        sa.Column("status", sa.String(40), nullable=False),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.UniqueConstraint("new_document_version_id", "historical_document_version_id", name="uq_document_comparison_pair"),
    )
    op.create_index("ix_document_comparisons_new_document", "document_comparisons", ["new_document_version_id"])

    op.create_table(
        "change_findings",
        sa.Column("id", sa.String(36), primary_key=True),
        sa.Column("comparison_id", sa.String(36), sa.ForeignKey("document_comparisons.id", ondelete="CASCADE"), nullable=False),
        sa.Column("previous_clause_id", sa.String(36), sa.ForeignKey("regulatory_clauses.id", ondelete="SET NULL")),
        sa.Column("updated_clause_id", sa.String(36), sa.ForeignKey("regulatory_clauses.id", ondelete="SET NULL")),
        sa.Column("classification", sa.String(80), nullable=False),
        sa.Column("previous_clause_number", sa.String(120)),
        sa.Column("updated_clause_number", sa.String(120)),
        sa.Column("previous_text", sa.Text()),
        sa.Column("updated_text", sa.Text()),
        sa.Column("previous_source_reference", sa.String(240)),
        sa.Column("updated_source_reference", sa.String(240)),
        sa.Column("change_summary", sa.Text(), nullable=False),
        sa.Column("why_it_matters", sa.Text(), nullable=False),
        sa.Column("affected_business_areas", sa.JSON(), nullable=False),
        sa.Column("affected_departments", sa.JSON(), nullable=False),
        sa.Column("recommended_actions", sa.JSON(), nullable=False),
        sa.Column("previous_deadline", sa.String(240)),
        sa.Column("updated_deadline", sa.String(240)),
        sa.Column("confidence", sa.Float(), nullable=False),
        sa.Column("evidence_verified", sa.Boolean(), nullable=False),
        sa.Column("needs_review", sa.Boolean(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
    )
    op.create_index("ix_change_findings_comparison", "change_findings", ["comparison_id"])
    op.create_index("ix_change_findings_classification", "change_findings", ["classification"])


def downgrade() -> None:
    op.drop_index("ix_change_findings_classification", table_name="change_findings")
    op.drop_index("ix_change_findings_comparison", table_name="change_findings")
    op.drop_table("change_findings")
    op.drop_index("ix_document_comparisons_new_document", table_name="document_comparisons")
    op.drop_table("document_comparisons")
    op.drop_index("ix_regulatory_references_document", table_name="regulatory_references")
    op.drop_table("regulatory_references")
    op.drop_column("obligations", "departments")
    op.drop_column("obligations", "affected_entities")
    op.drop_column("obligations", "obligation_type")
    op.drop_column("obligations", "clause_number")
    op.drop_column("obligations", "clause_id")
    op.drop_index("ix_regulatory_clauses_document", table_name="regulatory_clauses")
    op.drop_table("regulatory_clauses")
