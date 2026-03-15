from pydantic import BaseModel


class CheckAnswerRequest(BaseModel):
    exercise_type: str
    prompt: str
    user_answer: str
    answer_context: str


class CheckAnswerResponse(BaseModel):
    correct: bool
    score: float
    feedback: str
    corrected: str | None = None


class CheckpointMessage(BaseModel):
    scenario: str
    message: str
    history: list[dict] = []
