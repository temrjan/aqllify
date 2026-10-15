"""Authenticated course endpoints with server-owned grading and state."""

from typing import Annotated
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import FileResponse
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.router import get_current_user
from src.auth.schemas import TelegramUser
from src.database import get_db
from src.learning import ai, service
from src.learning.content import COURSE_DIR, get_course, get_lesson, placement_result
from src.learning.schemas import (
    AnswerResult,
    AttemptState,
    ChatInput,
    ChatReply,
    Completion,
    Course,
    Lesson,
    PlacementInput,
    PlacementResult,
    Progress,
    RateReview,
    ReviewCard,
    ReviewResult,
    StartAttempt,
    StrictModel,
    SubmitAnswer,
)

router = APIRouter(prefix="/learning", tags=["learning"])
User = Annotated[TelegramUser, Depends(get_current_user)]
Database = Annotated[AsyncSession, Depends(get_db)]


@router.get("/catalog")
def catalog(_user: User) -> Course:
    return get_course()


@router.get("/lessons/{lesson_id}")
def lesson(lesson_id: str, _user: User) -> Lesson:
    return get_lesson(lesson_id)


@router.get("/audio/{filename}")
def audio(filename: str) -> FileResponse:
    course = get_course()
    known = {phrase.audio for item in course.lessons for phrase in item.phrases}
    known.update(q.audio for q in course.placement if q.audio)
    if filename not in known:
        raise HTTPException(404, "Audio not found")
    return FileResponse(
        COURSE_DIR / "audio" / filename,
        media_type="audio/mpeg",
        headers={"Cache-Control": "public, max-age=31536000, immutable"},
    )


@router.post("/placement")
def placement(request: PlacementInput, _user: User) -> PlacementResult:
    return placement_result(request)


@router.post("/attempts")
async def start(request: StartAttempt, user: User, db: Database) -> AttemptState:
    return await service.start_attempt(db, user.id, request)


@router.get("/attempts/{attempt_id}")
async def attempt(attempt_id: UUID, user: User, db: Database) -> AttemptState:
    return await service.read_attempt(db, user.id, attempt_id)


@router.post("/attempts/{attempt_id}/answers")
async def answer(
    attempt_id: UUID, request: SubmitAnswer, user: User, db: Database
) -> AnswerResult:
    return await service.answer_attempt(db, user.id, attempt_id, request)


@router.post("/attempts/{attempt_id}/complete")
async def complete(
    attempt_id: UUID, user: User, db: Database, request: StrictModel | None = None
) -> Completion:
    return await service.complete_attempt(db, user.id, attempt_id)


@router.get("/progress")
async def progress(user: User, db: Database) -> Progress:
    return await service.get_progress(db, user.id)


@router.get("/review")
async def review(user: User, db: Database) -> list[ReviewCard]:
    return await service.get_reviews(db, user.id)


@router.post("/review")
async def rate(request: RateReview, user: User, db: Database) -> ReviewResult:
    return await service.rate_review(db, user.id, request)


@router.post("/dialogue")
async def dialogue(request: ChatInput, user: User) -> ChatReply:
    return await ai.chat(user.id, request)
