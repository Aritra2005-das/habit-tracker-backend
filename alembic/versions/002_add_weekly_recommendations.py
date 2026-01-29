"""Add weekly_recommendations table for auto-generated recommendations

Revision ID: 002_add_weekly_recommendations
Revises: 001_initial
Create Date: 2024-01-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '002_add_weekly_recommendations'
down_revision = '001_initial'
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create weekly_recommendations table
    op.create_table(
        'weekly_recommendations',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('week_start_date', sa.String(10), nullable=False),
        sa.Column('recommendation_type', sa.String(50), nullable=False),
        sa.Column('suggestion', sa.String(500), nullable=False),
        sa.Column('details', sa.String(1000), nullable=True),
        sa.Column('is_acted_upon', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('acted_upon_date', sa.DateTime(timezone=True), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
    )
    op.create_index(op.f('ix_weekly_recommendations_user_id'), 'weekly_recommendations', ['user_id'])
    op.create_index(op.f('ix_weekly_recommendations_habit_id'), 'weekly_recommendations', ['habit_id'])
    op.create_index(op.f('ix_weekly_recommendations_week_start_date'), 'weekly_recommendations', ['week_start_date'])


def downgrade() -> None:
    # Drop weekly_recommendations table
    op.drop_table('weekly_recommendations')
