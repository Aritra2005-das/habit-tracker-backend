"""Initial schema with users, habits, logs, and summaries

Revision ID: 001_initial
Revises: 
Create Date: 2024-01-28 00:00:00.000000

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '001_initial'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table(
        'users',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('email', sa.String(255), nullable=False),
        sa.Column('username', sa.String(100), nullable=False),
        sa.Column('hashed_password', sa.String(255), nullable=False),
        sa.Column('full_name', sa.String(255), nullable=True),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('email', name='uq_users_email'),
        sa.UniqueConstraint('username'),
    )
    op.create_index(op.f('ix_users_email'), 'users', ['email'], unique=True)
    op.create_index(op.f('ix_users_username'), 'users', ['username'], unique=True)

    # Create habits table
    op.create_table(
        'habits',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('name', sa.String(255), nullable=False),
        sa.Column('description', sa.Text(), nullable=True),
        sa.Column('category', sa.String(100), nullable=True),
        sa.Column('target_frequency', sa.Integer(), nullable=False, server_default='1'),
        sa.Column('frequency_unit', sa.String(20), nullable=False, server_default='day'),
        sa.Column('is_active', sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column('color', sa.String(7), nullable=True),
        sa.Column('icon', sa.String(100), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'name', name='uq_habits_user_id_name'),
    )
    op.create_index(op.f('ix_habits_user_id'), 'habits', ['user_id'])

    # Create habit_logs table
    op.create_table(
        'habit_logs',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('habit_id', sa.Integer(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('value', sa.Float(), nullable=True),
        sa.Column('notes', sa.Text(), nullable=True),
        sa.ForeignKeyConstraint(['habit_id'], ['habits.id'], ondelete='CASCADE'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('habit_id', 'user_id', 'date', name='uq_habit_logs_habit_id_user_id_date'),
    )
    op.create_index(op.f('ix_habit_logs_habit_id'), 'habit_logs', ['habit_id'])
    op.create_index(op.f('ix_habit_logs_user_id'), 'habit_logs', ['user_id'])
    op.create_index(op.f('ix_habit_logs_date'), 'habit_logs', ['date'])

    # Create day_summaries table
    op.create_table(
        'day_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('date', sa.Date(), nullable=False),
        sa.Column('total_habits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completed_habits', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('completion_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('streak_count', sa.Integer(), nullable=False, server_default='0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'date', name='uq_day_summaries_user_id_date'),
    )
    op.create_index(op.f('ix_day_summaries_user_id'), 'day_summaries', ['user_id'])
    op.create_index(op.f('ix_day_summaries_date'), 'day_summaries', ['date'])

    # Create week_summaries table
    op.create_table(
        'week_summaries',
        sa.Column('id', sa.Integer(), nullable=False),
        sa.Column('created_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('updated_at', sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column('user_id', sa.Integer(), nullable=False),
        sa.Column('week_start_date', sa.Date(), nullable=False),
        sa.Column('total_days_tracked', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('total_habits_completed', sa.Integer(), nullable=False, server_default='0'),
        sa.Column('average_completion_percentage', sa.Float(), nullable=False, server_default='0.0'),
        sa.Column('best_day_completion', sa.Float(), nullable=False, server_default='0.0'),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ondelete='CASCADE'),
        sa.PrimaryKeyConstraint('id'),
        sa.UniqueConstraint('user_id', 'week_start_date', name='uq_week_summaries_user_id_week_start_date'),
    )
    op.create_index(op.f('ix_week_summaries_user_id'), 'week_summaries', ['user_id'])
    op.create_index(op.f('ix_week_summaries_week_start_date'), 'week_summaries', ['week_start_date'])


def downgrade() -> None:
    # Drop all tables in reverse order
    op.drop_table('week_summaries')
    op.drop_table('day_summaries')
    op.drop_table('habit_logs')
    op.drop_table('habits')
    op.drop_table('users')
