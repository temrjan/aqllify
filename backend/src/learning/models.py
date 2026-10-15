"""Additive state; owners are verified Telegram IDs, not legacy users.id."""

from datetime import datetime
from uuid import UUID

from sqlalchemy import BigInteger, Boolean, DateTime, Float, Integer, String, Uuid
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from src.database import Base


class LearningAttempt(Base):
    __tablename__ = "learning_attempts"

    id: Mapped[UUID] = mapped_column(Uuid, primary_key=True)
    telegram_id: Mapped[int] = mapped_column(BigInteger, index=True)
    course_id: Mapped[str] = mapped_column(String(32))
    lesson_id: Mapped[str] = mapped_column(String(64))
    version: Mapped[str] = mapped_column(String(64))
    answers: Mapped[dict] = mapped_column(JSONB, default=dict)
    finalized: Mapped[bool] = mapped_column(Boolean, default=False)


class LearningProgress(Base):
    __tablename__ = "learning_progress"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    course_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(64))
    best_score: Mapped[float] = mapped_column(Float)
    completed: Mapped[bool] = mapped_column(Boolean)


class LearningReview(Base):
    __tablename__ = "learning_reviews"

    telegram_id: Mapped[int] = mapped_column(BigInteger, primary_key=True)
    course_id: Mapped[str] = mapped_column(String(32), primary_key=True)
    lesson_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    phrase_id: Mapped[str] = mapped_column(String(64), primary_key=True)
    version: Mapped[str] = mapped_column(String(64))
    due_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)
    successes: Mapped[int] = mapped_column(Integer, default=0)
    revision: Mapped[int] = mapped_column(Integer, default=0)
