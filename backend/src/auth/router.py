import structlog
from fastapi import APIRouter, Depends, Header, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.schemas import TelegramUser
from src.auth.service import validate_init_data, get_or_create_user
from src.database import get_db

logger = structlog.get_logger()
router = APIRouter(prefix="/auth", tags=["auth"])


async def get_current_user(
    x_telegram_init_data: str = Header(..., alias="X-Telegram-InitData"),
) -> TelegramUser:
    """Dependency: validate initData and return Telegram user."""
    try:
        return validate_init_data(x_telegram_init_data)
    except ValueError as e:
        logger.warning("auth_failed", reason=str(e))
        raise HTTPException(status_code=401, detail=str(e)) from e


@router.post("/login")
async def login(
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Validate initData, create user if needed, return profile."""
    user = await get_or_create_user(db, tg_user)
    return {"success": True, "user": user}
