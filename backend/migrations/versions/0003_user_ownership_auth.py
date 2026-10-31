"""Add Google users and per-user document ownership.

Revision ID: 0003_user_ownership_auth
Revises: 0002_doc_intel_comparison
"""
from alembic import op
import sqlalchemy as sa

revision = "0003_user_ownership_auth"
down_revision = "0002_doc_intel_comparison"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.String(length=36), primary_key=True),
        sa.Column("google_sub", sa.String(length=255), nullable=False),
        sa.Column("email", sa.String(length=320), nullable=False),
        sa.Column("display_name", sa.String(length=240), nullable=False),
        sa.Column("picture_url", sa.String(length=1000), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.UniqueConstraint("google_sub", name="uq_users_google_sub"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=False)

    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.add_column(sa.Column("owner_user_id", sa.String(length=36), nullable=True))
        batch_op.create_foreign_key(
            "fk_document_versions_owner_user_id_users",
            "users", ["owner_user_id"], ["id"], ondelete="SET NULL",
        )
        batch_op.drop_constraint("uq_document_versions_sha256", type_="unique")
        batch_op.create_unique_constraint("uq_document_versions_owner_sha256", ["owner_user_id", "sha256"])
        batch_op.create_index("ix_document_versions_owner", ["owner_user_id"], unique=False)


def downgrade() -> None:
    with op.batch_alter_table("document_versions") as batch_op:
        batch_op.drop_index("ix_document_versions_owner")
        batch_op.drop_constraint("uq_document_versions_owner_sha256", type_="unique")
        batch_op.create_unique_constraint("uq_document_versions_sha256", ["sha256"])
        batch_op.drop_constraint("fk_document_versions_owner_user_id_users", type_="foreignkey")
        batch_op.drop_column("owner_user_id")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
