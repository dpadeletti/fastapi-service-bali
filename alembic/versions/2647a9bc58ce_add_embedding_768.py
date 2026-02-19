"""add_embedding_768

Revision ID: 2647a9bc58ce
Revises: a2a06287c513
Create Date: 2026-02-16 15:44:18.241153

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = '2647a9bc58ce'
down_revision: Union[str, None] = 'a2a06287c513'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    try:
        import pgvector
        op.add_column('places', sa.Column('embedding', pgvector.sqlalchemy.Vector(dim=768), nullable=True))
    except Exception:
        pass  # pgvector non disponibile su questo RDS, skip


def downgrade() -> None:
    try:
        op.drop_column('places', 'embedding')
    except Exception:
        pass