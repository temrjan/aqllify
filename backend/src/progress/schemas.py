from datetime import date

from pydantic import BaseModel, Field


class ReviewCard(BaseModel):
    id: int
    word: str
    translation: str
    lesson_slug: str


class ReviewAnswer(BaseModel):
    card_id: int
    quality: int = Field(
        ge=0, le=5
    )  # SM-2 scale: 0=forgot, 3=correct with effort, 5=easy


class ReviewResult(BaseModel):
    card_id: int
    correct: bool
    xp_earned: int
    next_review: date
    interval_days: int


class UserStatsResponse(BaseModel):
    total_xp: int
    current_title: str
    next_title: str | None
    xp_to_next: int
    streak_days: int
    streak_freeze_available: bool
    words_learned: int
    lessons_completed: int


class AddXpRequest(BaseModel):
    lesson_slug: str = Field(max_length=100)
    xp: int = Field(ge=0, le=500)
    score: float | None = Field(default=None, ge=0, le=1.0)
