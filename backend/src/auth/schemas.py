from pydantic import BaseModel


class TelegramUser(BaseModel):
    id: int
    first_name: str
    last_name: str | None = None
    username: str | None = None
    language_code: str | None = None
    is_premium: bool | None = None
    photo_url: str | None = None


class UserResponse(BaseModel):
    id: int
    telegram_id: int
    first_name: str
    total_xp: int
    current_title: str
    streak_days: int
