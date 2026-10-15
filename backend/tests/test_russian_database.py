"""Real PostgreSQL contracts. Run explicitly with TEST_DATABASE_URL set.

Use a migrated disposable database; no production credentials or table resets.
Each test uses new synthetic Telegram identities and leaves them in that test DB.
"""

import asyncio
import hashlib
import hmac
import json
import os
import time
from datetime import timedelta
from urllib.parse import urlencode
from uuid import uuid4

import httpx
import pytest
from sqlalchemy import func, select, update
from sqlalchemy.ext.asyncio import async_sessionmaker, create_async_engine

from src.config import settings
from src.database import get_db
from src.learning import service
from src.learning.content import get_lesson
from src.learning.models import LearningProgress, LearningReview
from src.main import app

TEST_URL = os.environ.get("TEST_DATABASE_URL", "")
pytestmark = pytest.mark.skipif(
    not TEST_URL, reason="Set TEST_DATABASE_URL for real PostgreSQL checks"
)


def signed_header(owner: int) -> dict[str, str]:
    fields = {
        "auth_date": str(int(time.time())),
        "user": json.dumps({"id": owner, "first_name": "Test"}),
    }
    secret = hmac.new(
        b"WebAppData", settings.bot_token.encode(), hashlib.sha256
    ).digest()
    check = "\n".join(f"{key}={value}" for key, value in sorted(fields.items()))
    fields["hash"] = hmac.new(secret, check.encode(), hashlib.sha256).hexdigest()
    return {"X-Telegram-InitData": urlencode(fields)}


async def exercise_scenario(monkeypatch: pytest.MonkeyPatch) -> None:
    if "test" not in TEST_URL.rsplit("/", 1)[-1]:
        raise RuntimeError("Refusing a database not explicitly named for testing")
    engine = create_async_engine(TEST_URL)
    sessions = async_sessionmaker(engine, expire_on_commit=False)

    async def database():
        async with sessions() as db:
            yield db

    app.dependency_overrides[get_db] = database
    owner = uuid4().int % 10**12
    other = owner + 1
    headers = signed_header(owner)
    lesson = get_lesson("introductions")
    base = "/api/v1/learning"
    try:
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://test"
        ) as client:
            assert (await client.get(base + "/catalog")).status_code == 422
            assert (
                await client.get(
                    base + "/catalog", headers={"X-Telegram-InitData": "bad"}
                )
            ).status_code == 401
            catalog = await client.get(base + "/catalog", headers=headers)
            assert catalog.status_code == 200
            assert "accepted" not in catalog.json()["lessons"][0]["exercises"][0]
            media = await client.get(base + "/audio/" + lesson.phrases[0].audio)
            assert media.status_code == 200 and len(media.content) > 1000
            assert (
                await client.get(base + "/audio/not-allowed.mp3")
            ).status_code == 404

            async def start(lesson_id: str = lesson.id) -> str:
                attempt_id = str(uuid4())
                response = await client.post(
                    base + "/attempts",
                    headers=headers,
                    json={"id": attempt_id, "lesson_id": lesson_id},
                )
                assert response.status_code == 200, response.text
                return attempt_id

            first = await start()
            url = f"{base}/attempts/{first}"
            assert (
                await client.get(url, headers=signed_header(other))
            ).status_code == 404
            assert (
                await client.post(
                    base + "/attempts",
                    headers=signed_header(other),
                    json={"id": first, "lesson_id": lesson.id},
                )
            ).status_code == 404
            assert (
                await client.post(
                    base + "/attempts",
                    headers=headers,
                    json={"id": first, "lesson_id": "meetings"},
                )
            ).status_code == 409
            assert (
                await client.post(url + "/complete", headers=headers, json={})
            ).status_code == 409
            forged = await client.post(
                url + "/answers",
                headers=headers,
                json={
                    "exercise_id": "meaning",
                    "answer": "Salom!",
                    "correct": True,
                    "xp": 999,
                },
            )
            assert forged.status_code == 422
            assert (
                await client.post(
                    url + "/complete", headers=headers, json={"xp": 999, "score": 1}
                )
            ).status_code == 422
            assert (
                await client.post(
                    url + "/answers",
                    headers=headers,
                    json={"exercise_id": "unknown", "answer": "x"},
                )
            ).status_code == 404
            replay = await client.post(
                base + "/attempts",
                headers=headers,
                json={"id": first, "lesson_id": lesson.id},
            )
            assert replay.status_code == 200 and replay.json()["answers"] == {}
            first_body = {
                "exercise_id": lesson.exercises[0].id,
                "answer": lesson.exercises[0].accepted[0],
            }
            saved = await client.post(
                url + "/answers", headers=headers, json=first_body
            )
            repeated = await client.post(
                url + "/answers", headers=headers, json=first_body
            )
            assert saved.status_code == 200 and saved.json() == repeated.json()
            changed = await client.post(
                url + "/answers",
                headers=headers,
                json={
                    **first_body,
                    "answer": next(
                        v
                        for v in lesson.exercises[0].options
                        if v not in lesson.exercises[0].accepted
                    ),
                },
            )
            assert changed.status_code == 409
            assert (await client.get(url, headers=headers)).json()["answers"][
                "meaning"
            ]["correct"] is True
            for exercise in lesson.exercises[1:]:
                response = await client.post(
                    url + "/answers",
                    headers=headers,
                    json={"exercise_id": exercise.id, "answer": exercise.accepted[0]},
                )
                assert response.status_code == 200, response.text
            second = await start()
            for exercise in lesson.exercises:
                assert (
                    await client.post(
                        f"{base}/attempts/{second}/answers",
                        headers=headers,
                        json={
                            "exercise_id": exercise.id,
                            "answer": exercise.accepted[0],
                        },
                    )
                ).status_code == 200
            completions = await asyncio.gather(
                *[
                    client.post(
                        f"{base}/attempts/{aid}/complete", headers=headers, json={}
                    )
                    for aid in (first, first, second)
                ]
            )
            assert all(
                r.status_code == 200 and r.json()["total_xp"] == 40 for r in completions
            )
            assert (
                await client.post(url + "/complete", headers=headers, json={})
            ).json()["total_xp"] == 40
            async with sessions() as db:
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(LearningProgress)
                        .where(LearningProgress.telegram_id == owner)
                    )
                    == 1
                )
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(LearningReview)
                        .where(LearningReview.telegram_id == owner)
                    )
                    == 4
                )
            # A later unsuccessful attempt must not reduce prior mastery or grant XP.
            low = await start()
            for exercise in lesson.exercises:
                wrong = next(
                    (v for v in exercise.options if v not in exercise.accepted), "wrong"
                )
                assert (
                    await client.post(
                        f"{base}/attempts/{low}/answers",
                        headers=headers,
                        json={"exercise_id": exercise.id, "answer": wrong},
                    )
                ).status_code == 200
            low_result = await client.post(
                f"{base}/attempts/{low}/complete", headers=headers, json={}
            )
            assert low_result.json() == {"completed": False, "score": 0, "total_xp": 40}
            progress = (await client.get(base + "/progress", headers=headers)).json()
            assert progress["lessons"] == [
                {"lesson_id": "introductions", "completed": True, "best_score": 1}
            ]
            reviews = (await client.get(base + "/review", headers=headers)).json()
            assert len(reviews) == 4
            card = reviews[0]
            body = {key: card[key] for key in ("lesson_id", "phrase_id", "revision")}
            body["rating"] = "remembered"
            assert (
                await client.post(
                    base + "/review", headers=signed_header(other), json=body
                )
            ).status_code == 404
            rates = await asyncio.gather(
                *[
                    client.post(base + "/review", headers=headers, json=body)
                    for _ in range(2)
                ]
            )
            assert sorted(r.status_code for r in rates) == [200, 409]
            body["revision"] = 1
            assert (
                await client.post(base + "/review", headers=headers, json=body)
            ).status_code == 409
            async with sessions.begin() as db:
                await db.execute(
                    update(LearningReview)
                    .where(
                        LearningReview.telegram_id == owner,
                        LearningReview.phrase_id == card["phrase_id"],
                    )
                    .values(due_at=service.utc_now() - timedelta(seconds=1))
                )
            body["rating"] = "again"
            again = await client.post(base + "/review", headers=headers, json=body)
            assert again.status_code == 200 and again.json()["revision"] == 2
            async with sessions() as db:
                row = (
                    await db.scalars(
                        select(LearningReview).where(
                            LearningReview.telegram_id == owner,
                            LearningReview.phrase_id == card["phrase_id"],
                        )
                    )
                ).one()
                assert row.successes == 0
                assert (
                    timedelta(minutes=9)
                    < row.due_at - service.utc_now()
                    <= timedelta(minutes=10)
                )
            assert (
                await client.get(base + "/progress", headers=signed_header(other))
            ).json() == {"lessons": [], "total_xp": 0, "due_count": 0}

            # Inject failure after actual database writes: the real transaction must roll back.
            failed_lesson = get_lesson("meetings")
            failed = await start(failed_lesson.id)
            for exercise in failed_lesson.exercises:
                await client.post(
                    f"{base}/attempts/{failed}/answers",
                    headers=headers,
                    json={"exercise_id": exercise.id, "answer": exercise.accepted[0]},
                )

            async def fail_xp(*_args):
                raise RuntimeError("injected transaction failure")

            with monkeypatch.context() as context:
                context.setattr(service, "course_xp", fail_xp)
                with pytest.raises(RuntimeError, match="injected transaction failure"):
                    await client.post(
                        f"{base}/attempts/{failed}/complete", headers=headers, json={}
                    )
            async with sessions() as db:
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(LearningProgress)
                        .where(
                            LearningProgress.telegram_id == owner,
                            LearningProgress.lesson_id == failed_lesson.id,
                        )
                    )
                    == 0
                )
                assert (
                    await db.scalar(
                        select(func.count())
                        .select_from(LearningReview)
                        .where(
                            LearningReview.telegram_id == owner,
                            LearningReview.lesson_id == failed_lesson.id,
                        )
                    )
                    == 0
                )
            assert (
                await client.get(f"{base}/attempts/{failed}", headers=headers)
            ).json()["finalized"] is False
            assert (
                await client.post(
                    f"{base}/attempts/{failed}/complete", headers=headers, json={}
                )
            ).json()["total_xp"] == 80
    finally:
        app.dependency_overrides.pop(get_db, None)
        await engine.dispose()


def test_postgres_attempts_reviews_and_rollback(
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    asyncio.run(exercise_scenario(monkeypatch))
