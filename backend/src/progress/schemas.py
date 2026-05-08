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
    # Pattern blocks path-traversal at input layer; safe_path is the final
    # guard. Allowed: lowercase letters, digits, `_`, `-`, `/`
    # (e.g. "block-1/01-salomlashish"). `-` at end of class = literal.
    lesson_slug: str = Field(max_length=100, pattern=r"^[a-z0-9][a-z0-9_/-]{0,99}$")
    xp: int = Field(ge=0, le=500)
    score: float | None = Field(default=None, ge=0, le=1.0)
