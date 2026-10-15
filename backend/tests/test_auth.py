"""Tests for Telegram Mini App initData validation (audit B4 + B12)."""

import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import pytest

from src.auth.service import validate_init_data
from src.config import settings

TEST_BOT_TOKEN = "1234567890:TEST_BOT_TOKEN_FOR_HMAC_GENERATION"


def _build_init_data(
    bot_token: str,
    user: dict,
    auth_date: int | None = None,
    tamper_hash: bool = False,
) -> str:
    """Construct a signed initData string the way Telegram does."""
    auth_date = auth_date if auth_date is not None else int(time.time())
    user_json = json.dumps(user, separators=(",", ":"))

    fields = {"auth_date": str(auth_date), "user": user_json}
    data_check_string = "\n".join(f"{k}={v}" for k, v in sorted(fields.items()))

    secret = hmac.new(b"WebAppData", bot_token.encode(), hashlib.sha256).digest()
    signature = hmac.new(secret, data_check_string.encode(), hashlib.sha256).hexdigest()
    if tamper_hash:
        signature = "0" * len(signature)

    return urlencode({**fields, "hash": signature})


@pytest.fixture(autouse=True)
def _patch_bot_token(monkeypatch: pytest.MonkeyPatch) -> None:
    """validate_init_data reads settings.bot_token at call time."""
    monkeypatch.setattr(settings, "bot_token", TEST_BOT_TOKEN)


class TestInitDataValidation:
    """HMAC validation, replay window, tamper resistance (B4)."""

    def test_accepts_fresh_valid_init_data(self) -> None:
        init_data = _build_init_data(TEST_BOT_TOKEN, {"id": 42, "first_name": "Alice"})
        user = validate_init_data(init_data)
        assert user.id == 42
        assert user.first_name == "Alice"

    def test_rejects_expired_auth_date(self) -> None:
        # 2 hours old — exceeds the new 3600s default (B4 fix)
        old = int(time.time()) - 7200
        init_data = _build_init_data(
            TEST_BOT_TOKEN, {"id": 42, "first_name": "Alice"}, auth_date=old
        )
        with pytest.raises(ValueError, match="expired"):
            validate_init_data(init_data)

    def test_default_ttl_is_one_hour(self) -> None:
        # Regression guard: previous default was 86400 (24h).
        # Audit B4 narrowed it. Pin the value.
        import inspect

        sig = inspect.signature(validate_init_data)
        assert sig.parameters["max_age_seconds"].default == 3600

    def test_rejects_tampered_hash(self) -> None:
        init_data = _build_init_data(
            TEST_BOT_TOKEN, {"id": 42, "first_name": "Alice"}, tamper_hash=True
        )
        with pytest.raises(ValueError, match="Invalid hash"):
            validate_init_data(init_data)

    def test_rejects_missing_hash(self) -> None:
        init_data = urlencode(
            {
                "auth_date": str(int(time.time())),
                "user": json.dumps({"id": 42, "first_name": "Alice"}),
            }
        )
        with pytest.raises(ValueError, match="Missing hash"):
            validate_init_data(init_data)

    def test_rejects_modified_field_with_unchanged_hash(self) -> None:
        # Sign one user, then swap user_id without re-signing.
        init_data = _build_init_data(TEST_BOT_TOKEN, {"id": 42, "first_name": "Alice"})
        forged = init_data.replace("%22id%22%3A42", "%22id%22%3A99")
        assert forged != init_data, (
            "test setup: payload mutation must change the string"
        )
        with pytest.raises(ValueError, match="Invalid hash"):
            validate_init_data(forged)
