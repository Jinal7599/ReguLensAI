"""Add user-managed compliance disposition to change findings.

Revision ID: 0004_compliance_status
Revises: 0003_user_ownership_auth
"""
from alembic import op
import sqlalchemy as sa

revision = "0004_compliance_status"
down_revision = "0003_user_ownership_auth"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.add_column(
        "change_findings",
        sa.Column("compliance_status", sa.String(length=24), server_default="open", nullable=False),
    )


def downgrade() -> None:
    op.drop_column("change_findings", "compliance_status")
