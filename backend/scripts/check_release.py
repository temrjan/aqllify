"""Read-only release smoke check. Never logs credentials or creates user state."""

import asyncio
import hashlib
import hmac
import json
import time
from urllib.parse import urlencode

import httpx
from sqlalchemy import text

from src.config import settings
from src.database import engine
from src.learning.content import get_course
from src.lessons.service import list_lessons


def require(condition: bool, message: str) -> None:
    if not condition:
        raise RuntimeError(message)


async def main() -> None:
    course = get_course()
    require(len(course.lessons) == 12, "Incomplete Russian course")
    require(bool(list_lessons("uzlearn")), "Legacy catalog unavailable")
    async with engine.connect() as db:
        require(
            await db.scalar(text("SELECT version_num FROM alembic_version")) == "002",
            "Unexpected migration revision",
        )
        for table in ("learning_attempts", "learning_progress", "learning_reviews"):
            require(
                await db.scalar(text("SELECT to_regclass(:name)"), {"name": table})
                is not None,
                "Missing learning table",
            )

    # This synthetic identity is used only for GET requests. It is never logged
    # in, registered, graded or written to storage.
    data = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": 900000000000001, "first_name": "Release check"}),
    }
    secret = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    data["hash"] = hmac.new(
        secret,
        "\n".join(f"{key}={data[key]}" for key in sorted(data)).encode(),
        hashlib.sha256,
    ).hexdigest()
    headers = {"X-Telegram-InitData": urlencode(data)}
    async with httpx.AsyncClient(
        base_url="http://localhost:8000", timeout=10, trust_env=False
    ) as client:
        response = await client.get("/api/v1/learning/catalog")
        require(response.status_code == 422, "Missing auth must be rejected")
        response = await client.get("/api/v1/learning/catalog", headers=headers)
        response.raise_for_status()
        catalog = response.json()
        require(catalog["version"] == course.version, "Catalog version mismatch")
        require(len(catalog["lessons"]) == 12, "Catalog missing lessons")
        for lesson in catalog["lessons"]:
            require("scenario" not in lesson, "Scenario leaked")
            for exercise in lesson["exercises"]:
                require("accepted" not in exercise, "Answer key leaked")
        for path in ("progress", "review", "lessons/introductions"):
            response = await client.get(f"/api/v1/learning/{path}", headers=headers)
            response.raise_for_status()
        audio = course.lessons[0].phrases[0].audio
        response = await client.get(f"/api/v1/learning/audio/{audio}")
        response.raise_for_status()
        require(len(response.content) > 100, "Empty audio")
        require(
            response.headers.get("content-type", "").startswith("audio/mpeg"),
            "Invalid audio response",
        )
    await engine.dispose()
    print(
        "Release check passed: schema, authenticated curriculum/state reads, audio, legacy catalog"
    )


if __name__ == "__main__":
    asyncio.run(main())
