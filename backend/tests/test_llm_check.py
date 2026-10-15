"""Tests for LLM check_answer — must never leak answer_context (audit B3)."""

import asyncio
import json
from types import SimpleNamespace
from unittest.mock import AsyncMock, patch

import pytest
from src.services.llm import check_answer
from structlog.testing import capture_logs

# Sentinel must not appear in any exception text, log record, or return value
# when the LLM call fails. This is the core invariant of the B3 fix.
SECRET_ANSWER = "TOTALLY_SECRET_ANSWER_DO_NOT_LEAK_42"


def _fake_response(content: str) -> SimpleNamespace:
    """Build a minimal stand-in for openai's ChatCompletion response."""
    return SimpleNamespace(
        choices=[SimpleNamespace(message=SimpleNamespace(content=content))]
    )


def _assert_logged_failure_without_leak(cap_logs: list[dict]) -> None:
    """Sanity-check that the failure was logged AND the secret is absent."""
    assert any(log.get("event") == "llm_check_failed" for log in cap_logs), (
        "expected llm_check_failed event in captured logs — "
        "test cannot validate leakage if the log was not captured"
    )
    for log in cap_logs:
        assert SECRET_ANSWER not in str(log), f"answer_context leaked in log: {log}"


@pytest.fixture
def mock_openai():
    """Patch the module-level AsyncOpenAI client's create() method."""
    with patch(
        "src.services.llm.client.chat.completions.create",
        new_callable=AsyncMock,
    ) as mock:
        yield mock


class TestCheckAnswerLeakage:
    """check_answer must propagate failures and never expose answer_context."""

    def test_propagates_on_openai_failure_without_leaking(self, mock_openai) -> None:
        mock_openai.side_effect = RuntimeError("openai down")
        with (
            capture_logs() as cap_logs,
            pytest.raises(RuntimeError) as exc_info,
        ):
            asyncio.run(check_answer("open_translate", "Q", "wrong", SECRET_ANSWER))
        assert SECRET_ANSWER not in str(exc_info.value)
        _assert_logged_failure_without_leak(cap_logs)

    def test_propagates_on_json_decode_error_without_leaking(self, mock_openai) -> None:
        mock_openai.return_value = _fake_response("not-valid-json{")
        with (
            capture_logs() as cap_logs,
            pytest.raises(json.JSONDecodeError) as exc_info,
        ):
            asyncio.run(check_answer("open_translate", "Q", "wrong", SECRET_ANSWER))
        assert SECRET_ANSWER not in str(exc_info.value)
        _assert_logged_failure_without_leak(cap_logs)


class TestCheckAnswerHappyPath:
    """Sanity: successful LLM response still returns the expected dict shape."""

    def test_returns_parsed_dict_on_valid_json(self, mock_openai) -> None:
        mock_openai.return_value = _fake_response(
            '{"correct": true, "score": 1.0, "feedback": "ok", "corrected": null}'
        )
        result = asyncio.run(check_answer("open_translate", "Q", "salom", "salom"))
        assert result == {
            "correct": True,
            "score": 1.0,
            "feedback": "ok",
            "corrected": None,
        }
