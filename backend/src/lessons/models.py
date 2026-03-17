from typing import Literal

from pydantic import BaseModel, Field


class CheckAnswerRequest(BaseModel):
    exercise_type: str = Field(max_length=50)
    prompt: str = Field(max_length=500)
    user_answer: str = Field(max_length=1000)
    answer_context: str = Field(max_length=1000)


class CheckAnswerResponse(BaseModel):
    correct: bool
    score: float
    feedback: str
    corrected: str | None = None


class HistoryMessage(BaseModel):
    role: Literal["user", "assistant"]
    content: str = Field(max_length=1000)


class CheckpointMessage(BaseModel):
    scenario: str = Field(max_length=2000)
    message: str = Field(max_length=500)
    history: list[HistoryMessage] = Field(default_factory=list, max_length=20)
