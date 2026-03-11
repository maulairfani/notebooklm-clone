"""add_video_settings_columns

Revision ID: e5f6a7b8c9d0
Revises: d4e5f6a7b8c9
Create Date: 2026-03-07 10:00:00.000000

"""
from typing import Sequence, Union

import sqlalchemy as sa
from alembic import op


# revision identifiers, used by Alembic.
revision: str = 'e5f6a7b8c9d0'
down_revision: Union[str, None] = 'd4e5f6a7b8c9'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.add_column('videos', sa.Column('structure', sa.String(length=50), nullable=False, server_default='comprehensive'))
    op.add_column('videos', sa.Column('visual_style', sa.String(length=50), nullable=False, server_default='white_board'))
    op.add_column('videos', sa.Column('custom_prompt', sa.Text(), nullable=True))


def downgrade() -> None:
    op.drop_column('videos', 'custom_prompt')
    op.drop_column('videos', 'visual_style')
    op.drop_column('videos', 'structure')
