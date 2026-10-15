from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8")

    # App
    app_env: str = "development"
    app_name: str = "aqllify"
    api_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    # Database
    database_url: str = (
        "postgresql+asyncpg://tutor:tutor_password@localhost:5432/tutor_db"
    )

    # Telegram
    bot_token: str = ""
    admin_telegram_ids: str = ""

    # LLM
    openai_api_key: str = ""
    llm_model: str = "gpt-6-luna"
    llm_reasoning_effort: Literal["none", "low", "medium", "high", "xhigh", "max"] = (
        "medium"
    )
    # Completion budget includes reasoning tokens as well as visible text.
    llm_max_completion_tokens: int = Field(default=4096, ge=1)

    # TTS
    tts_lang: str = "uz"

    @property
    def is_development(self) -> bool:
        return self.app_env == "development"

    @property
    def admin_ids(self) -> list[int]:
        if not self.admin_telegram_ids:
            return []
        return [int(x.strip()) for x in self.admin_telegram_ids.split(",")]


settings = Settings()
