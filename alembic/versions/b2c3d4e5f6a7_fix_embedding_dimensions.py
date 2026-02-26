"""fix embedding dimensions 768 to 1024

Revision ID: b2c3d4e5f6a7
Revises: a1b2c3d4e5f6
Create Date: 2026-02-26 20:00:00.000000

"""
from typing import Sequence, Union
from alembic import op

revision: str = 'b2c3d4e5f6a7'
down_revision: Union[str, None] = 'a1b2c3d4e5f6'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # Titan Embeddings v2 restituisce 1024 dimensioni di default
    op.execute("ALTER TABLE places ALTER COLUMN embedding TYPE vector(1024)")


def downgrade() -> None:
    op.execute("ALTER TABLE places ALTER COLUMN embedding TYPE vector(768)")
