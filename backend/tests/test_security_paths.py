"""Tests for path-traversal hardening (audit findings B1, B2)."""

from pathlib import Path

import pytest
from pydantic import ValidationError
from src.lessons.service import COURSES_DIR, safe_path
from src.progress.schemas import AddXpRequest


class TestSafePath:
    """safe_path must reject any resolved path that escapes the base."""

    def test_blocks_dotdot_traversal(self) -> None:
        with pytest.raises(ValueError):
            safe_path(COURSES_DIR, "..", "..", "etc")

    def test_blocks_absolute_override(self) -> None:
        # Path("/etc") joined to base resolves to "/etc" on POSIX
        # (absolute components replace base). is_relative_to catches this.
        with pytest.raises(ValueError):
            safe_path(COURSES_DIR, "/etc/passwd")

    def test_blocks_sibling_prefix(self, tmp_path: Path) -> None:
        # Regression for B2: previous startswith() check passed
        # "courses_secret" against base "courses".
        base = tmp_path / "courses"
        base.mkdir()
        sibling = tmp_path / "courses_secret"
        sibling.mkdir()
        with pytest.raises(ValueError):
            safe_path(base, "..", "courses_secret")

    def test_allows_valid_subpath(self) -> None:
        result = safe_path(COURSES_DIR, "uzlearn", "block-1", "01-salomlashish")
        assert result.is_relative_to(COURSES_DIR.resolve())


class TestAddXpRequestSlug:
    """Pydantic regex blocks malformed slugs at the input layer."""

    def test_accepts_valid_slug(self) -> None:
        req = AddXpRequest(lesson_slug="block-1/01-salomlashish", xp=50)
        assert req.lesson_slug == "block-1/01-salomlashish"

    def test_rejects_dotdot(self) -> None:
        with pytest.raises(ValidationError):
            AddXpRequest(lesson_slug="../../etc", xp=1)

    def test_rejects_absolute(self) -> None:
        with pytest.raises(ValidationError):
            AddXpRequest(lesson_slug="/etc/passwd", xp=1)

    def test_rejects_uppercase(self) -> None:
        with pytest.raises(ValidationError):
            AddXpRequest(lesson_slug="Block-1/01-FOO", xp=1)

    def test_rejects_backslash(self) -> None:
        with pytest.raises(ValidationError):
            AddXpRequest(lesson_slug="block-1\\01-foo", xp=1)
