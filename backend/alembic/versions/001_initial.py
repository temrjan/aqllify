"""Initial schema: users, stats, progress, srs_cards

Revision ID: 001
Revises: None
Create Date: 2026-03-15
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa

revision: str = "001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "telegram_id", sa.BigInteger, unique=True, nullable=False, index=True
        ),
        sa.Column("first_name", sa.String(100), nullable=False),
        sa.Column("daily_goal_minutes", sa.Integer, server_default="10"),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now()
        ),
    )

    op.create_table(
        "user_stats",
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            primary_key=True,
        ),
        sa.Column("total_xp", sa.Integer, server_default="0"),
        sa.Column("current_title", sa.String(20), server_default="spark"),
        sa.Column("streak_days", sa.Integer, server_default="0"),
        sa.Column("last_activity_date", sa.Date, nullable=True),
        sa.Column("streak_freeze_available", sa.Boolean, server_default="true"),
    )

    op.create_table(
        "user_lesson_progress",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("lesson_slug", sa.String(100), nullable=False),
        sa.Column("completed", sa.Boolean, server_default="false"),
        sa.Column("score", sa.Float, nullable=True),
        sa.Column("xp_earned", sa.Integer, server_default="0"),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
    )

    op.create_table(
        "srs_cards",
        sa.Column("id", sa.BigInteger, primary_key=True, autoincrement=True),
        sa.Column(
            "user_id",
            sa.BigInteger,
            sa.ForeignKey("users.id", ondelete="CASCADE"),
            nullable=False,
            index=True,
        ),
        sa.Column("word", sa.String(500), nullable=False),
        sa.Column("translation", sa.String(500), nullable=False),
        sa.Column("lesson_slug", sa.String(100), nullable=False),
        sa.Column("ease_factor", sa.Float, server_default="2.5"),
        sa.Column("interval_days", sa.Integer, server_default="0"),
        sa.Column("next_review", sa.Date, nullable=False),
        sa.Column("correct_count", sa.Integer, server_default="0"),
        sa.Column("incorrect_count", sa.Integer, server_default="0"),
    )


def downgrade() -> None:
    op.drop_table("srs_cards")
    op.drop_table("user_lesson_progress")
    op.drop_table("user_stats")
    op.drop_table("users")
