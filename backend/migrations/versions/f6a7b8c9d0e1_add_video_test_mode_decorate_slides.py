"""add_video_test_mode_decorate_slides

Revision ID: f6a7b8c9d0e1
Revises: e5f6a7b8c9d0
Create Date: 2026-03-11 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'f6a7b8c9d0e1'
down_revision: Union[str, None] = 'e5f6a7b8c9d0'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('test_mode', sa.Boolean(), nullable=False, server_default='false'))
    op.add_column('videos', sa.Column('decorate_slides', sa.Boolean(), nullable=False, server_default='true'))


def downgrade() -> None:
    op.drop_column('videos', 'decorate_slides')
    op.drop_column('videos', 'test_mode')
