import json
from datetime import date, datetime, timezone
from pathlib import Path

from sqlalchemy import func, select
from sqlalchemy.ext.asyncio import AsyncSession

from src.progress.models import SrsCard, User, UserLessonProgress, UserStats
from src.progress.schemas import ReviewCard, ReviewResult

COURSES_DIR = Path(__file__).parent.parent.parent.parent / 'courses'

# SM-2 algorithm constants
MIN_EASE = 1.3
INITIAL_EASE = 2.5

# Title thresholds (must match course.json)
TITLES = [
    ('spark', 0),
    ('pulse', 500),
    ('wave', 1500),
    ('flash', 3000),
    ('storm', 6000),
    ('blaze', 10000),
    ('titan', 16000),
    ('phantom', 24000),
    ('nova', 35000),
    ('apex', 50000),
]


# ═══════════════════════════════════════════════════════════════
# SM-2 Spaced Repetition
# ═══════════════════════════════════════════════════════════════

def sm2_calculate(
    quality: int,
    ease_factor: float,
    interval_days: int,
    correct_count: int,
) -> tuple[float, int]:
    """SM-2 algorithm. Returns (new_ease_factor, new_interval_days).

    quality: 0-5 rating
        0-2 = incorrect (reset interval)
        3   = correct with difficulty
        4   = correct
        5   = easy
    """
    # Update ease factor
    new_ease = ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02))
    new_ease = max(MIN_EASE, new_ease)

    # Calculate new interval
    if quality < 3:
        # Incorrect — reset
        new_interval = 1
    elif correct_count == 0:
        new_interval = 1
    elif correct_count == 1:
        new_interval = 3
    else:
        new_interval = round(interval_days * new_ease)

    return new_ease, new_interval


async def get_due_cards(
    db: AsyncSession,
    user_id: int,
    limit: int = 15,
) -> list[ReviewCard]:
    """Get cards due for review today."""
    today = date.today()
    result = await db.execute(
        select(SrsCard)
        .where(SrsCard.user_id == user_id, SrsCard.next_review <= today)
        .order_by(SrsCard.next_review)
        .limit(limit)
    )
    cards = result.scalars().all()

    return [
        ReviewCard(
            id=card.id,
            word=card.word,
            translation=card.translation,
            lesson_slug=card.lesson_slug,
        )
        for card in cards
    ]


async def review_card(
    db: AsyncSession,
    user_id: int,
    card_id: int,
    quality: int,
) -> ReviewResult:
    """Process a review answer using SM-2 algorithm."""
    result = await db.execute(
        select(SrsCard).where(SrsCard.id == card_id, SrsCard.user_id == user_id)
    )
    card = result.scalar_one_or_none()
    if not card:
        raise ValueError('Card not found')

    correct = quality >= 3

    # SM-2 calculation
    new_ease, new_interval = sm2_calculate(
        quality=quality,
        ease_factor=card.ease_factor,
        interval_days=card.interval_days,
        correct_count=card.correct_count,
    )

    # Update card
    card.ease_factor = new_ease
    card.interval_days = new_interval
    card.next_review = date.today() + __import__('datetime').timedelta(days=new_interval)

    if correct:
        card.correct_count += 1
        xp = 10
    else:
        card.incorrect_count += 1
        xp = 0

    await db.commit()

    return ReviewResult(
        card_id=card.id,
        correct=correct,
        xp_earned=xp,
        next_review=card.next_review,
        interval_days=new_interval,
    )


async def create_cards_from_lesson(
    db: AsyncSession,
    user_id: int,
    course: str,
    lesson_slug: str,
) -> int:
    """Create SRS cards for all phrases in a lesson. Returns count created."""
    # Load lesson phrases from exercises.json
    exercises_path = COURSES_DIR / course / lesson_slug / 'exercises.json'
    lesson_path = COURSES_DIR / course / lesson_slug / 'lesson.md'

    cards_created = 0
    today = date.today()

    # Extract phrases from lesson.md table
    if lesson_path.exists():
        text = lesson_path.read_text(encoding='utf-8')
        in_table = False

        for line in text.split('\n'):
            stripped = line.strip()
            if stripped.startswith('|') and 'Узбекский' in stripped:
                in_table = True
                continue
            if in_table and stripped.startswith('|---'):
                continue
            if in_table and stripped.startswith('|'):
                cells = [c.strip() for c in stripped.split('|')[1:-1]]
                # 3-col table: uzbek | cyrillic | russian
                # 2-col table: uzbek | russian
                if len(cells) >= 3 and cells[0] and cells[2]:
                    word, translation = cells[0], cells[2]
                elif len(cells) >= 2 and cells[0] and cells[1]:
                    word, translation = cells[0], cells[1]
                else:
                    continue
                # Check if card already exists
                existing = await db.execute(
                    select(SrsCard).where(
                        SrsCard.user_id == user_id,
                        SrsCard.word == word,
                    )
                )
                if not existing.scalar_one_or_none():
                    card = SrsCard(
                        user_id=user_id,
                        word=word,
                        translation=translation,
                        lesson_slug=lesson_slug,
                        next_review=today,
                    )
                    db.add(card)
                    cards_created += 1
            elif in_table and not stripped.startswith('|'):
                in_table = False

    await db.commit()
    return cards_created


# ═══════════════════════════════════════════════════════════════
# XP + Streak + Titles
# ═══════════════════════════════════════════════════════════════

def get_title_for_xp(xp: int) -> str:
    """Get title based on total XP."""
    title = 'spark'
    for name, threshold in TITLES:
        if xp >= threshold:
            title = name
    return title


def get_next_title_info(xp: int) -> tuple[str | None, int]:
    """Returns (next_title_name, xp_needed). None if at max."""
    for i, (name, threshold) in enumerate(TITLES):
        if xp < threshold:
            return name, threshold - xp
    return None, 0


async def add_xp(
    db: AsyncSession,
    user_id: int,
    xp: int,
    lesson_slug: str | None = None,
    score: float | None = None,
) -> dict:
    """Add XP, update streak, check title promotion."""
    result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    stats = result.scalar_one_or_none()
    if not stats:
        raise ValueError('User stats not found')

    old_title = stats.current_title
    today = date.today()

    # Update XP
    stats.total_xp += xp

    # Update streak
    if stats.last_activity_date == today:
        pass  # Already active today
    elif stats.last_activity_date == today - __import__('datetime').timedelta(days=1):
        stats.streak_days += 1
        stats.streak_freeze_available = True  # Reset freeze weekly? Simplified: always available
    elif stats.last_activity_date is None:
        stats.streak_days = 1
    else:
        # Missed a day
        if stats.streak_freeze_available:
            stats.streak_freeze_available = False
            stats.streak_days += 1  # Freeze saves streak
        else:
            stats.streak_days = 1  # Reset

    stats.last_activity_date = today

    # Streak bonus XP
    stats.total_xp += 20  # Daily streak bonus

    # Check title promotion
    new_title = get_title_for_xp(stats.total_xp)
    promoted = new_title != old_title
    if promoted:
        stats.current_title = new_title

    # Save lesson progress (upsert — no duplicates)
    if lesson_slug:
        existing_progress = await db.execute(
            select(UserLessonProgress).where(
                UserLessonProgress.user_id == user_id,
                UserLessonProgress.lesson_slug == lesson_slug,
            )
        )
        progress = existing_progress.scalar_one_or_none()
        if progress:
            progress.score = max(progress.score or 0, score or 0)
            progress.xp_earned = max(progress.xp_earned, xp)
            progress.completed_at = datetime.now(tz=timezone.utc)
        else:
            db.add(UserLessonProgress(
                user_id=user_id,
                lesson_slug=lesson_slug,
                completed=True,
                score=score,
                xp_earned=xp,
                completed_at=datetime.now(tz=timezone.utc),
            ))

    await db.commit()

    next_title, xp_to_next = get_next_title_info(stats.total_xp)

    return {
        'total_xp': stats.total_xp,
        'xp_earned': xp + 20,  # lesson + streak bonus
        'streak_days': stats.streak_days,
        'current_title': stats.current_title,
        'promoted': promoted,
        'old_title': old_title if promoted else None,
        'next_title': next_title,
        'xp_to_next': xp_to_next,
    }


async def get_user_stats(db: AsyncSession, user_id: int) -> dict:
    """Get full user statistics."""
    result = await db.execute(
        select(UserStats).where(UserStats.user_id == user_id)
    )
    stats = result.scalar_one_or_none()
    if not stats:
        raise ValueError('User stats not found')

    # Count words and lessons
    words_count = await db.execute(
        select(func.count()).where(SrsCard.user_id == user_id)
    )
    lessons_count = await db.execute(
        select(func.count()).where(
            UserLessonProgress.user_id == user_id,
            UserLessonProgress.completed.is_(True),
        )
    )

    next_title, xp_to_next = get_next_title_info(stats.total_xp)

    return {
        'total_xp': stats.total_xp,
        'current_title': stats.current_title,
        'next_title': next_title,
        'xp_to_next': xp_to_next,
        'streak_days': stats.streak_days,
        'streak_freeze_available': stats.streak_freeze_available,
        'words_learned': words_count.scalar() or 0,
        'lessons_completed': lessons_count.scalar() or 0,
    }
