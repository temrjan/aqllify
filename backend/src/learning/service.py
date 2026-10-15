"""Transactional attempt and review operations; no legacy progress writes."""

from datetime import UTC, datetime, timedelta
from uuid import UUID

from fastapi import HTTPException
from sqlalchemy import func, select
from sqlalchemy.dialects.postgresql import insert
from sqlalchemy.ext.asyncio import AsyncSession

from src.learning.content import get_course, get_exercise, get_lesson, is_correct
from src.learning.models import LearningAttempt, LearningProgress, LearningReview
from src.learning.schemas import (
    AnswerResult,
    AttemptState,
    Completion,
    LessonProgress,
    Progress,
    RateReview,
    ReviewCard,
    ReviewResult,
    StartAttempt,
    SubmitAnswer,
)


def utc_now() -> datetime:
    return datetime.now(UTC)


def check_version(version: str) -> None:
    if version != get_course().version:
        raise HTTPException(409, "Course changed; start a new attempt")


def attempt_state(attempt: LearningAttempt) -> AttemptState:
    return AttemptState(
        id=attempt.id,
        lesson_id=attempt.lesson_id,
        version=attempt.version,
        answers=attempt.answers,
        finalized=attempt.finalized,
    )


async def owned_attempt(
    db: AsyncSession, owner: int, attempt_id: UUID, *, lock: bool = False
) -> LearningAttempt:
    query = select(LearningAttempt).where(
        LearningAttempt.id == attempt_id,
        LearningAttempt.telegram_id == owner,
        LearningAttempt.course_id == "russian",
    )
    if lock:
        query = query.with_for_update()
    attempt = (await db.execute(query)).scalar_one_or_none()
    if attempt is None:
        raise HTTPException(404, "Attempt not found")
    check_version(attempt.version)
    return attempt


async def start_attempt(
    db: AsyncSession, owner: int, request: StartAttempt
) -> AttemptState:
    lesson = get_lesson(request.lesson_id)
    async with db.begin():
        await db.execute(
            insert(LearningAttempt)
            .values(
                id=request.id,
                telegram_id=owner,
                course_id="russian",
                lesson_id=lesson.id,
                version=get_course().version,
                answers={},
                finalized=False,
            )
            .on_conflict_do_nothing(index_elements=["id"])
        )
        attempt = await owned_attempt(db, owner, request.id, lock=True)
        if attempt.lesson_id != lesson.id:
            raise HTTPException(409, "Attempt belongs to another lesson")
        return attempt_state(attempt)


async def read_attempt(db: AsyncSession, owner: int, attempt_id: UUID) -> AttemptState:
    async with db.begin():
        return attempt_state(await owned_attempt(db, owner, attempt_id))


async def answer_attempt(
    db: AsyncSession, owner: int, attempt_id: UUID, request: SubmitAnswer
) -> AnswerResult:
    if not request.answer.strip():
        raise HTTPException(422, "Answer must not be blank")
    async with db.begin():
        attempt = await owned_attempt(db, owner, attempt_id, lock=True)
        exercise = get_exercise(get_lesson(attempt.lesson_id), request.exercise_id)
        if exercise.kind == "choice" and request.answer not in exercise.options:
            raise HTTPException(422, "Choose an available option")
        previous = attempt.answers.get(exercise.id)
        if previous is not None:
            if previous["answer"] != request.answer:
                raise HTTPException(409, "Answer already saved; start fresh practice")
            return AnswerResult.model_validate(previous)
        if attempt.finalized:
            raise HTTPException(409, "Attempt already completed")
        correct = is_correct(exercise, request.answer)
        result = AnswerResult(
            answer=request.answer,
            correct=correct,
            feedback=("To‘g‘ri! " if correct else "Yana mashq qilib ko‘ring. ")
            + exercise.explanation,
            corrected=None if correct else exercise.accepted[0],
        )
        attempt.answers = {**attempt.answers, exercise.id: result.model_dump()}
        return result


async def course_xp(db: AsyncSession, owner: int) -> int:
    count = await db.scalar(
        select(func.count())
        .select_from(LearningProgress)
        .where(
            LearningProgress.telegram_id == owner,
            LearningProgress.course_id == "russian",
            LearningProgress.completed.is_(True),
        )
    )
    return int(count or 0) * 40


async def complete_attempt(
    db: AsyncSession, owner: int, attempt_id: UUID
) -> Completion:
    async with db.begin():
        attempt = await owned_attempt(db, owner, attempt_id, lock=True)
        lesson = get_lesson(attempt.lesson_id)
        if set(attempt.answers) != {ex.id for ex in lesson.exercises}:
            raise HTTPException(409, "Answer every exercise before completing")
        score = sum(result["correct"] for result in attempt.answers.values()) / len(
            lesson.exercises
        )
        completed = score >= 0.8
        statement = insert(LearningProgress).values(
            telegram_id=owner,
            course_id="russian",
            lesson_id=lesson.id,
            version=get_course().version,
            best_score=score,
            completed=completed,
        )
        statement = statement.on_conflict_do_update(
            index_elements=["telegram_id", "course_id", "lesson_id"],
            set_={
                "best_score": func.greatest(
                    LearningProgress.best_score, statement.excluded.best_score
                ),
                "completed": LearningProgress.completed | statement.excluded.completed,
            },
            where=LearningProgress.version == get_course().version,
        ).returning(LearningProgress.lesson_id)
        if (await db.execute(statement)).scalar_one_or_none() is None:
            raise HTTPException(409, "Saved course version needs migration")
        if completed:
            await db.execute(
                insert(LearningReview)
                .values(
                    [
                        {
                            "telegram_id": owner,
                            "course_id": "russian",
                            "lesson_id": lesson.id,
                            "phrase_id": phrase.id,
                            "version": get_course().version,
                            "due_at": utc_now(),
                            "successes": 0,
                            "revision": 0,
                        }
                        for phrase in lesson.phrases
                    ]
                )
                .on_conflict_do_nothing(
                    index_elements=[
                        "telegram_id",
                        "course_id",
                        "lesson_id",
                        "phrase_id",
                    ]
                )
            )
        attempt.finalized = True
        return Completion(
            completed=completed, score=score, total_xp=await course_xp(db, owner)
        )


async def get_progress(db: AsyncSession, owner: int) -> Progress:
    async with db.begin():
        rows = (
            await db.scalars(
                select(LearningProgress)
                .where(
                    LearningProgress.telegram_id == owner,
                    LearningProgress.course_id == "russian",
                )
                .order_by(LearningProgress.lesson_id)
            )
        ).all()
        for row in rows:
            check_version(row.version)
        due = await db.scalar(
            select(func.count())
            .select_from(LearningReview)
            .where(
                LearningReview.telegram_id == owner,
                LearningReview.course_id == "russian",
                LearningReview.due_at <= utc_now(),
            )
        )
        return Progress(
            lessons=[
                LessonProgress(
                    lesson_id=row.lesson_id,
                    completed=row.completed,
                    best_score=row.best_score,
                )
                for row in rows
            ],
            total_xp=sum(row.completed for row in rows) * 40,
            due_count=int(due or 0),
        )


async def get_reviews(db: AsyncSession, owner: int) -> list[ReviewCard]:
    async with db.begin():
        rows = (
            await db.scalars(
                select(LearningReview)
                .where(
                    LearningReview.telegram_id == owner,
                    LearningReview.course_id == "russian",
                    LearningReview.due_at <= utc_now(),
                )
                .order_by(
                    LearningReview.due_at,
                    LearningReview.lesson_id,
                    LearningReview.phrase_id,
                )
                .limit(50)
            )
        ).all()
        cards = []
        for row in rows:
            check_version(row.version)
            phrase = next(
                (p for p in get_lesson(row.lesson_id).phrases if p.id == row.phrase_id),
                None,
            )
            if phrase is None:
                raise HTTPException(409, "Review content changed")
            cards.append(
                ReviewCard(
                    lesson_id=row.lesson_id,
                    phrase_id=row.phrase_id,
                    russian=phrase.russian,
                    uzbek=phrase.uzbek,
                    audio=phrase.audio,
                    revision=row.revision,
                )
            )
        return cards


async def rate_review(
    db: AsyncSession, owner: int, request: RateReview
) -> ReviewResult:
    async with db.begin():
        card = (
            await db.scalars(
                select(LearningReview)
                .where(
                    LearningReview.telegram_id == owner,
                    LearningReview.course_id == "russian",
                    LearningReview.lesson_id == request.lesson_id,
                    LearningReview.phrase_id == request.phrase_id,
                )
                .with_for_update()
            )
        ).one_or_none()
        if card is None:
            raise HTTPException(404, "Review card not found")
        check_version(card.version)
        now = utc_now()
        if card.revision != request.revision or card.due_at > now:
            raise HTTPException(409, "Review already saved; reload the due cards")
        if request.rating == "again":
            card.successes = 0
            card.due_at = now + timedelta(minutes=10)
        else:
            card.successes += 1
            days = (1, 3, 7, 14)[min(card.successes - 1, 3)]
            card.due_at = now + timedelta(days=days)
        card.revision += 1
        return ReviewResult(revision=card.revision, due_at=card.due_at)
