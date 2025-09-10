"""Create user_progress_log table

Revision ID: 20250910115755
Revises:
Create Date: 2025-09-10 11:57:55.336009

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = 'rev_20250910115755'
down_revision = None
branch_labels = None
depends_on = None


def upgrade(op=None):
    """
    Upgrade the database to the latest revision.
    """
    op.create_table(
        'user_progress_log',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),
        sa.Column('user_id', sa.Integer(), sa.ForeignKey('users.id', ondelete='CASCADE')),
        sa.Column('challenge_id', sa.Integer(), sa.ForeignKey('challenges.id', ondelete='CASCADE')),
        sa.Column('category', sa.String(length=80), nullable=True),
        sa.Column('status', sa.String(length=32), nullable=True),
        sa.Column('date', sa.DateTime(), nullable=True, server_default=sa.func.now())
    )


def downgrade(op=None):
    """
    Downgrade the database to the previous revision.
    """
    op.drop_table('user_progress_log')
