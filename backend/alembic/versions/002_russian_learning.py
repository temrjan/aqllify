"""Add course-scoped Russian learning state without changing legacy records."""

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision = "002"
down_revision = "001"
branch_labels = None
depends_on = None


def upgrade() -> None:
    op.create_table(
        "learning_attempts",
        sa.Column("id", sa.Uuid(), primary_key=True),
        sa.Column("telegram_id", sa.BigInteger(), nullable=False),
        sa.Column("course_id", sa.String(32), nullable=False),
        sa.Column("lesson_id", sa.String(64), nullable=False),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("answers", postgresql.JSONB(), nullable=False),
        sa.Column("finalized", sa.Boolean(), nullable=False),
    )
    op.create_index(
        "ix_learning_attempts_telegram_id", "learning_attempts", ["telegram_id"]
    )
    op.create_table(
        "learning_progress",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("course_id", sa.String(32), primary_key=True),
        sa.Column("lesson_id", sa.String(64), primary_key=True),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("best_score", sa.Float(), nullable=False),
        sa.Column("completed", sa.Boolean(), nullable=False),
    )
    op.create_table(
        "learning_reviews",
        sa.Column("telegram_id", sa.BigInteger(), primary_key=True),
        sa.Column("course_id", sa.String(32), primary_key=True),
        sa.Column("lesson_id", sa.String(64), primary_key=True),
        sa.Column("phrase_id", sa.String(64), primary_key=True),
        sa.Column("version", sa.String(64), nullable=False),
        sa.Column("due_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("successes", sa.Integer(), nullable=False),
        sa.Column("revision", sa.Integer(), nullable=False),
    )
    op.create_index("ix_learning_reviews_due_at", "learning_reviews", ["due_at"])


def downgrade() -> None:
    op.drop_table("learning_reviews")
    op.drop_table("learning_progress")
    op.drop_table("learning_attempts")
