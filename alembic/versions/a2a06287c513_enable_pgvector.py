"""enable_pgvector

Revision ID: a2a06287c513
Revises: 3e9e19912d63
Create Date: 2026-02-16 14:40:35.091071

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'a2a06287c513'
down_revision: Union[str, None] = '3e9e19912d63'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        op.execute("CREATE EXTENSION IF NOT EXISTS vector")
    except Exception:
        pass  # pgvector non disponibile su questo RDS, skip


def downgrade() -> None:
    try:
        op.execute("DROP EXTENSION IF EXISTS vector")
    except Exception:
        pass