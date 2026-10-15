"""Load and validate an immutable course release, separate from legacy parsing."""

import unicodedata
from functools import lru_cache
from pathlib import Path

from fastapi import HTTPException

from src.learning.schemas import (
    Course,
    Exercise,
    Lesson,
    PlacementInput,
    PlacementResult,
)

COURSE_DIR = Path(__file__).resolve().parents[3] / "courses" / "russian"


@lru_cache(maxsize=1)
def get_course() -> Course:
    """Fail loudly for invalid deployment content; cache only validated releases."""
    course = Course.model_validate_json((COURSE_DIR / "course.json").read_text())
    audio = {p.audio for lesson in course.lessons for p in lesson.phrases}
    audio.update(q.audio for q in course.placement if q.audio)
    for name in audio:
        if not (COURSE_DIR / "audio" / name).is_file():
            raise ValueError(f"Missing course audio: {name}")
    return course


def get_lesson(lesson_id: str) -> Lesson:
    for lesson in get_course().lessons:
        if lesson.id == lesson_id:
            return lesson
    raise HTTPException(404, "Lesson not found")


def get_exercise(lesson: Lesson, exercise_id: str) -> Exercise:
    for exercise in lesson.exercises:
        if exercise.id == exercise_id:
            return exercise
    raise HTTPException(404, "Exercise not found")


def normalize(answer: str) -> str:
    """Normalize presentation only; retain words, negation and numbers."""
    value = unicodedata.normalize("NFC", answer).casefold().replace("ё", "е")
    value = " ".join(value.split())
    return value.strip(' .,!?:;"«»“”„…')


def is_correct(exercise: Exercise, answer: str) -> bool:
    return normalize(answer) in {normalize(value) for value in exercise.accepted}


def placement_result(request: PlacementInput) -> PlacementResult:
    questions = get_course().placement
    if set(request.answers) != {q.id for q in questions}:
        raise HTTPException(422, "Answer every placement question")
    skills = {"reading": 0, "listening": 0, "response": 0}
    for question in questions:
        answer = request.answers[question.id]
        if answer not in question.options:
            raise HTTPException(422, "Choose an available option")
        skills[question.skill] += int(is_correct(question, answer))
    score = sum(skills.values())
    level = "beginner" if score <= 2 else "intermediate" if score <= 4 else "advanced"
    return PlacementResult(
        level=level, score=score, skills=skills, assisted=request.assisted
    )
