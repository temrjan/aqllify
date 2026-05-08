import time
from collections import defaultdict

import structlog
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.router import get_current_user
from src.auth.schemas import TelegramUser
from src.auth.service import get_or_create_user
from src.database import get_db
from src.lessons.models import (
    CheckAnswerRequest,
    CheckAnswerResponse,
    CheckpointMessage,
)
from src.lessons.schemas import LessonContent, LessonListItem
from src.lessons.service import get_lesson, list_lessons
from src.progress.models import UserLessonProgress
from src.services.llm import check_answer, checkpoint_dialog

logger = structlog.get_logger()
router = APIRouter(prefix="/lessons", tags=["lessons"])

# In-memory rate limiter for LLM endpoints (per user, sliding window)
_llm_requests: dict[int, list[float]] = defaultdict(list)
MAX_LLM_PER_MINUTE = 20


def _check_rate_limit(user_id: int) -> None:
    """Raise 429 if user exceeds LLM rate limit."""
    now = time.time()
    window = _llm_requests[user_id]
    _llm_requests[user_id] = [t for t in window if now - t < 60]
    if len(_llm_requests[user_id]) >= MAX_LLM_PER_MINUTE:
        raise HTTPException(status_code=429, detail="Too many requests")
    _llm_requests[user_id].append(now)


@router.get("/{course}")
async def get_lessons_list(
    course: str,
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[LessonListItem]:
    """List all lessons for a course, with user completion status."""
    try:
        lessons = list_lessons(course)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Course {course} not found")

    user = await get_or_create_user(db, tg_user)
    result = await db.execute(
        select(UserLessonProgress).where(
            UserLessonProgress.user_id == user["id"],
            UserLessonProgress.completed.is_(True),
        )
    )
    completed = {p.lesson_slug: p for p in result.scalars().all()}

    for lesson in lessons:
        progress = completed.get(lesson.slug)
        if progress:
            lesson.completed = True
            lesson.score = progress.score

    return lessons


@router.get("/{course}/{block_slug}/{lesson_slug}")
async def get_lesson_content(
    course: str,
    block_slug: str,
    lesson_slug: str,
    _user: TelegramUser = Depends(get_current_user),
) -> LessonContent:
    """Get a single lesson with content and exercises."""
    slug = f"{block_slug}/{lesson_slug}"
    try:
        return get_lesson(course, slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f"Lesson {slug} not found")


@router.post("/check-answer")
async def check_student_answer(
    req: CheckAnswerRequest,
    tg_user: TelegramUser = Depends(get_current_user),
) -> CheckAnswerResponse:
    """Check student answer using LLM."""
    _check_rate_limit(tg_user.id)
    try:
        result = await check_answer(
            exercise_type=req.exercise_type,
            prompt=req.prompt,
            user_answer=req.user_answer,
            answer_context=req.answer_context,
        )
    except HTTPException:
        # Let typed HTTP errors (e.g. future upstream-rate-limit 429) through unchanged.
        raise
    except Exception as e:
        # Never leak answer_context: any LLM-side failure → opaque 503.
        raise HTTPException(
            status_code=503,
            detail="LLM service temporarily unavailable",
        ) from e
    logger.info(
        "answer_checked",
        user_id=tg_user.id,
        type=req.exercise_type,
        correct=result.get("correct"),
    )
    return CheckAnswerResponse(**result)


@router.post("/checkpoint-dialog")
async def checkpoint_chat(
    req: CheckpointMessage,
    tg_user: TelegramUser = Depends(get_current_user),
) -> dict:
    """AI conversation for checkpoint role-play."""
    _check_rate_limit(tg_user.id)
    reply = await checkpoint_dialog(
        scenario=req.scenario,
        user_message=req.message,
        history=[m.model_dump() for m in req.history],
    )
    return {"reply": reply}
