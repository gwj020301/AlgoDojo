"""add knowledge_tips to problems

Revision ID: e692ef8d14c2
Revises: e77de128c045
Create Date: 2026-06-21 01:45:10.574054

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision: str = "e692ef8d14c2"
down_revision: str | None = "e77de128c045"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    op.add_column(
        "problems",
        sa.Column(
            "knowledge_tips",
            sa.JSON().with_variant(postgresql.JSONB(astext_type=sa.Text()), "postgresql"),
            nullable=False,
            server_default=sa.text("'[]'"),
        ),
    )
    # 仅用于回填存量行，去掉默认值由应用层负责写入
    op.alter_column("problems", "knowledge_tips", server_default=None)


def downgrade() -> None:
    op.drop_column("problems", "knowledge_tips")
