"""Additive upgrade preserves real legacy rows; requires an empty test database."""

import asyncio
import os
import subprocess
import sys
from pathlib import Path

import asyncpg
import pytest

URL = os.environ.get("TEST_MIGRATION_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not URL, reason="Set TEST_MIGRATION_DATABASE_URL to an empty disposable database"
)
BACKEND = Path(__file__).resolve().parents[1]


def migrate(revision, direction="upgrade"):
    result = subprocess.run(
        [sys.executable, "-m", "alembic", direction, revision],
        cwd=BACKEND,
        env={**os.environ, "PYTHONPATH": str(BACKEND), "DATABASE_URL": URL},
        text=True,
        capture_output=True,
        check=False,
    )
    assert result.returncode == 0, result.stdout + result.stderr


def test_legacy_preserved_by_upgrade():
    if "test" not in URL.rsplit("/", 1)[-1]:
        raise RuntimeError("Only disposable test databases are allowed")

    async def scenario():
        db = await asyncpg.connect(
            URL.replace("postgresql+asyncpg://", "postgresql://")
        )
        try:
            assert await db.fetchval("SELECT to_regclass('alembic_version')") is None, (
                "Use a new empty database"
            )
            await asyncio.to_thread(migrate, "001")
            await db.execute("""
                INSERT INTO users (id, telegram_id, first_name) VALUES (90001, 70001, 'Legacy');
                INSERT INTO user_stats (user_id, total_xp, streak_days) VALUES (90001, 321, 7);
                INSERT INTO user_lesson_progress (user_id, lesson_slug, completed, score, xp_earned)
                VALUES (90001, 'block-1/01-salomlashish', true, 0.9, 50);
                INSERT INTO srs_cards (user_id, word, translation, lesson_slug, next_review)
                VALUES (90001, 'Salom', 'Привет', 'block-1/01-salomlashish', '2026-10-15');
            """)
            tables = ("users", "user_stats", "user_lesson_progress", "srs_cards")
            before = {
                table: await db.fetch(f"SELECT * FROM {table}") for table in tables
            }
            await asyncio.to_thread(migrate, "head")
            after = {
                table: await db.fetch(f"SELECT * FROM {table}") for table in tables
            }
            assert before == after
            assert await db.fetchval("SELECT version_num FROM alembic_version") == "002"
            for table in ("learning_attempts", "learning_progress", "learning_reviews"):
                assert await db.fetchval(f"SELECT count(*) FROM {table}") == 0
            await asyncio.to_thread(migrate, "001", "downgrade")
            restored = {
                table: await db.fetch(f"SELECT * FROM {table}") for table in tables
            }
            assert restored == before
            assert await db.fetchval("SELECT to_regclass('learning_attempts')") is None
        finally:
            await db.close()

    asyncio.run(scenario())
