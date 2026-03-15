from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession

from src.auth.router import get_current_user
from src.auth.schemas import TelegramUser
from src.auth.service import get_or_create_user
from src.database import get_db
from src.progress.schemas import AddXpRequest, ReviewAnswer, ReviewCard, ReviewResult
from src.progress.service import (
    add_xp,
    create_cards_from_lesson,
    get_due_cards,
    get_user_stats,
    review_card,
)

router = APIRouter(prefix='/progress', tags=['progress'])


@router.get('/stats')
async def stats(
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Get user stats: XP, title, streak, words, lessons."""
    user = await get_or_create_user(db, tg_user)
    return await get_user_stats(db, user['id'])


@router.get('/review')
async def get_review_cards(
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> list[ReviewCard]:
    """Get SRS cards due for review today."""
    user = await get_or_create_user(db, tg_user)
    return await get_due_cards(db, user['id'])


@router.post('/review')
async def submit_review(
    answer: ReviewAnswer,
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> ReviewResult:
    """Submit a review answer, update SRS intervals."""
    user = await get_or_create_user(db, tg_user)
    try:
        result = await review_card(db, user['id'], answer.card_id, answer.quality)
    except ValueError as e:
        raise HTTPException(status_code=404, detail=str(e))

    # Add XP if correct
    if result.xp_earned > 0:
        await add_xp(db, user['id'], result.xp_earned)

    return result


@router.post('/complete-lesson')
async def complete_lesson(
    req: AddXpRequest,
    course: str = 'uzlearn',
    tg_user: TelegramUser = Depends(get_current_user),
    db: AsyncSession = Depends(get_db),
) -> dict:
    """Complete a lesson: add XP, create SRS cards, update streak."""
    user = await get_or_create_user(db, tg_user)

    # Create SRS cards from lesson phrases
    cards_created = await create_cards_from_lesson(db, user['id'], course, req.lesson_slug)

    # Add XP + update streak
    result = await add_xp(db, user['id'], req.xp, req.lesson_slug, req.score)

    return {
        **result,
        'cards_created': cards_created,
    }
