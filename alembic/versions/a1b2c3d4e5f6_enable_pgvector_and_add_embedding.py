"""enable pgvector and add embedding column

Revision ID: a1b2c3d4e5f6
Revises: 2647a9bc58ce
Create Date: 2026-02-24 10:00:00.000000

"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

revision: str = 'a1b2c3d4e5f6'
down_revision: Union[str, None] = '2647a9bc58ce'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Abilita l'estensione pgvector (supportata da Aurora PostgreSQL 15.x)
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")

    # Aggiunge la colonna embedding (768 dimensioni — Titan Embeddings v2)
    op.execute("ALTER TABLE places ADD COLUMN IF NOT EXISTS embedding vector(768)")


def downgrade() -> None:
    op.execute("ALTER TABLE places DROP COLUMN IF EXISTS embedding")
    # Non droppiamo l'estensione: potrebbe essere usata da altre tabelle
