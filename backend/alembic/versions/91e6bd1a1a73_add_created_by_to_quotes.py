"""add created_by to quotes

Revision ID: 91e6bd1a1a73
Revises: d566e872c03b
Create Date: 2026-07-15 00:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '91e6bd1a1a73'
down_revision: Union[str, Sequence[str], None] = 'd566e872c03b'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    """Upgrade schema."""
    op.add_column(
        'quotes',
        sa.Column('created_by', sa.String(length=255), nullable=True)
    )
    op.create_index(
        op.f('ix_quotes_created_by'),
        'quotes',
        ['created_by'],
        unique=False
    )


def downgrade() -> None:
    """Downgrade schema."""
    op.drop_index(op.f('ix_quotes_created_by'), table_name='quotes')
    op.drop_column('quotes', 'created_by')
