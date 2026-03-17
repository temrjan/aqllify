import hashlib
import hmac
import json
from datetime import datetime, timezone
from urllib.parse import parse_qs, unquote

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import TelegramUser
from src.config import settings


def validate_init_data(
    init_data: str,
    max_age_seconds: int = 86400,
) -> TelegramUser:
    """Validate Telegram Mini App initData and extract user."""
    parsed = parse_qs(init_data)

    received_hash = parsed.get("hash", [None])[0]
    if not received_hash:
        raise ValueError("Missing hash")

    # Build data check string (sorted, without hash)
    data_check_arr = []
    for key, values in sorted(parsed.items()):
        if key != "hash":
            data_check_arr.append(f"{key}={values[0]}")

    data_check_string = "\n".join(data_check_arr)

    # Create secret key
    secret_key = hmac.new(
        b"WebAppData",
        settings.bot_token.encode(),
        hashlib.sha256,
    ).digest()

    # Calculate hash
    calculated_hash = hmac.new(
        secret_key,
        data_check_string.encode(),
        hashlib.sha256,
    ).hexdigest()

    # Compare (timing-safe)
    if not hmac.compare_digest(calculated_hash, received_hash):
        raise ValueError("Invalid hash")

    # Check auth_date
    auth_date = int(parsed.get("auth_date", ["0"])[0])
    current_time = int(datetime.now(tz=timezone.utc).timestamp())

    if current_time - auth_date > max_age_seconds:
        raise ValueError("Init data expired")

    # Parse user
    user_str = parsed.get("user", [None])[0]
    if not user_str:
        raise ValueError("User data missing")

    user_data = json.loads(unquote(user_str))
    return TelegramUser(**user_data)


async def get_or_create_user(
    db: AsyncSession,
    tg_user: TelegramUser,
) -> dict:
    """Get existing user or create new one. Returns user dict."""
    from src.progress.models import User, UserStats

    result = await db.execute(select(User).where(User.telegram_id == tg_user.id))
    user = result.scalar_one_or_none()

    if not user:
        user = User(
            telegram_id=tg_user.id,
            first_name=tg_user.first_name,
        )
        db.add(user)
        await db.flush()

        stats = UserStats(user_id=user.id)
        db.add(stats)
        await db.commit()
        await db.refresh(user)

    return {
        "id": user.id,
        "telegram_id": user.telegram_id,
        "first_name": user.first_name,
    }
