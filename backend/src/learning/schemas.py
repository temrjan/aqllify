"""Validated content and HTTP contracts for the Russian course."""

from datetime import datetime
from typing import Annotated, Literal
from uuid import UUID

from pydantic import BaseModel, ConfigDict, Field, field_validator, model_validator

Identifier = Annotated[str, Field(pattern=r"^[a-z0-9][a-z0-9-]{0,63}$")]
AnswerText = Annotated[str, Field(min_length=1, max_length=500)]
LevelId = Literal["beginner", "intermediate", "advanced"]


class StrictModel(BaseModel):
    model_config = ConfigDict(extra="forbid")


class Phrase(StrictModel):
    id: Identifier
    russian: str = Field(min_length=1)
    uzbek: str = Field(min_length=1)
    audio: str = Field(pattern=r"^[a-f0-9]{16}\.mp3$")


class Exercise(StrictModel):
    id: Identifier
    kind: Literal["choice", "text"]
    prompt: str = Field(min_length=1)
    options: list[str] = Field(default_factory=list)
    accepted: list[str] = Field(min_length=1, exclude=True)
    explanation: str = Field(min_length=1, exclude=True)
    transfer: bool = False

    @model_validator(mode="after")
    def validate_answers(self) -> "Exercise":
        if any(not answer.strip() for answer in self.accepted):
            raise ValueError("Empty accepted answer")
        if self.kind == "choice" and (
            len(self.options) < 2
            or len(set(self.options)) != len(self.options)
            or any(answer not in self.options for answer in self.accepted)
        ):
            raise ValueError("Invalid choice answers")
        return self


class DialogLine(StrictModel):
    speaker: str
    russian: str
    uzbek: str


class Lesson(StrictModel):
    id: Identifier
    order: int = Field(ge=1)
    title: str
    goal: str
    phrases: list[Phrase] = Field(min_length=4)
    explanation: str
    dialogue: list[DialogLine] = Field(min_length=2)
    exercises: list[Exercise] = Field(min_length=4)
    scenario: str = Field(exclude=True)

    @model_validator(mode="after")
    def unique_items(self) -> "Lesson":
        for items in (self.phrases, self.exercises):
            if len({item.id for item in items}) != len(items):
                raise ValueError("Duplicate item ID")
        if not any(ex.transfer for ex in self.exercises):
            raise ValueError("Missing transfer task")
        return self


class Unit(StrictModel):
    title: str
    task: str


class Level(StrictModel):
    id: LevelId
    title: str
    description: str
    available: bool
    entry: list[str]
    units: list[Unit] = Field(min_length=4)
    completion: list[str]


class PlacementQuestion(Exercise):
    skill: Literal["reading", "listening", "response"]
    audio: str | None = Field(default=None, pattern=r"^[a-f0-9]{16}\.mp3$")
    transcript: str | None = None


class Course(StrictModel):
    id: Literal["russian"]
    version: str = Field(min_length=1, max_length=64)
    title: str
    description: str
    alphabet: list[Unit]
    levels: list[Level]
    placement: list[PlacementQuestion] = Field(min_length=6, max_length=6)
    lessons: list[Lesson] = Field(min_length=12, max_length=12)

    @model_validator(mode="after")
    def validate_catalog(self) -> "Course":
        if {level.id for level in self.levels} != {
            "beginner",
            "intermediate",
            "advanced",
        } or len(self.levels) != 3:
            raise ValueError("Expected three distinct levels")
        for items in (self.lessons, self.placement):
            if len({item.id for item in items}) != len(items):
                raise ValueError("Duplicate catalog ID")
        if len({lesson.order for lesson in self.lessons}) != len(self.lessons):
            raise ValueError("Duplicate lesson order")
        for skill in ("reading", "listening", "response"):
            if sum(q.skill == skill for q in self.placement) != 2:
                raise ValueError("Expected two questions per skill")
        if any(
            q.skill == "listening" and not (q.audio and q.transcript)
            for q in self.placement
        ):
            raise ValueError("Listening questions need audio and transcript")
        return self


class StartAttempt(StrictModel):
    id: UUID
    lesson_id: Identifier


class SubmitAnswer(StrictModel):
    exercise_id: Identifier
    answer: AnswerText


class AnswerResult(StrictModel):
    answer: str
    correct: bool
    feedback: str
    corrected: str | None = None


class AttemptState(StrictModel):
    id: UUID
    lesson_id: str
    version: str
    answers: dict[str, AnswerResult]
    finalized: bool


class Completion(StrictModel):
    completed: bool
    score: float
    total_xp: int


class LessonProgress(StrictModel):
    lesson_id: str
    completed: bool
    best_score: float


class Progress(StrictModel):
    lessons: list[LessonProgress]
    total_xp: int
    due_count: int


class ReviewCard(StrictModel):
    lesson_id: str
    phrase_id: str
    russian: str
    uzbek: str
    audio: str
    revision: int


class RateReview(StrictModel):
    lesson_id: Identifier
    phrase_id: Identifier
    revision: int = Field(ge=0)
    rating: Literal["again", "remembered"]


class ReviewResult(StrictModel):
    revision: int
    due_at: datetime


class PlacementInput(StrictModel):
    answers: dict[str, AnswerText]
    assisted: bool = False


class PlacementResult(StrictModel):
    level: LevelId
    score: int
    skills: dict[str, int]
    assisted: bool


class ChatMessage(StrictModel):
    role: Literal["user", "assistant"]
    content: AnswerText


class ChatInput(StrictModel):
    lesson_id: Identifier
    message: AnswerText
    history: list[ChatMessage] = Field(default_factory=list, max_length=8)

    @field_validator("message")
    @classmethod
    def nonblank_message(cls, value: str) -> str:
        if not value.strip():
            raise ValueError("Message must not be blank")
        return value


class ChatReply(StrictModel):
    reply: str = Field(min_length=1, max_length=500)
    feedback: str = Field(min_length=1, max_length=600)
