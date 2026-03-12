"""add podcasts table

Revision ID: c5a710109d24
Revises: f6a7b8c9d0e1
Create Date: 2026-03-12 00:11:00.853471

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'c5a710109d24'
down_revision: Union[str, None] = 'f6a7b8c9d0e1'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table('podcasts',
    sa.Column('id', sa.Uuid(), nullable=False),
    sa.Column('notebook_id', sa.Uuid(), nullable=False),
    sa.Column('title', sa.String(length=255), nullable=False),
    sa.Column('status', sa.String(length=50), nullable=False),
    sa.Column('language', sa.String(length=20), nullable=False),
    sa.Column('format', sa.String(length=50), nullable=False),
    sa.Column('length', sa.String(length=50), nullable=False),
    sa.Column('custom_prompt', sa.Text(), nullable=True),
    sa.Column('host_voice', sa.String(length=50), nullable=False),
    sa.Column('guest_voice', sa.String(length=50), nullable=False),
    sa.Column('test_mode', sa.Boolean(), nullable=False),
    sa.Column('file_path', sa.String(length=500), nullable=True),
    sa.Column('error_message', sa.Text(), nullable=True),
    sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.text('now()'), nullable=False),
    sa.ForeignKeyConstraint(['notebook_id'], ['notebooks.id'], ondelete='CASCADE'),
    sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_podcasts_notebook_id'), 'podcasts', ['notebook_id'], unique=False)


def downgrade() -> None:
    op.drop_index(op.f('ix_podcasts_notebook_id'), table_name='podcasts')
    op.drop_table('podcasts')
