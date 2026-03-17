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

router = APIRouter(prefix="/lessons", tags=["lessons"])


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
    _user: TelegramUser = Depends(get_current_user),
) -> CheckAnswerResponse:
    """Check student answer using LLM."""
    result = await check_answer(
        exercise_type=req.exercise_type,
        prompt=req.prompt,
        user_answer=req.user_answer,
        answer_context=req.answer_context,
    )
    return CheckAnswerResponse(**result)


@router.post("/checkpoint-dialog")
async def checkpoint_chat(
    req: CheckpointMessage,
    _user: TelegramUser = Depends(get_current_user),
) -> dict:
    """AI conversation for checkpoint role-play."""
    reply = await checkpoint_dialog(
        scenario=req.scenario,
        user_message=req.message,
        history=req.history,
    )
    return {"reply": reply}
