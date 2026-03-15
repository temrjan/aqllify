from fastapi import APIRouter, Depends, HTTPException

from src.auth.router import get_current_user
from src.auth.schemas import TelegramUser
from src.lessons.schemas import LessonContent, LessonListItem
from src.lessons.service import get_lesson, list_lessons

router = APIRouter(prefix='/lessons', tags=['lessons'])


@router.get('/{course}')
async def get_lessons_list(
    course: str,
    _user: TelegramUser = Depends(get_current_user),
) -> list[LessonListItem]:
    """List all lessons for a course."""
    try:
        return list_lessons(course)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'Course {course} not found')


@router.get('/{course}/{block_slug}/{lesson_slug}')
async def get_lesson_content(
    course: str,
    block_slug: str,
    lesson_slug: str,
    _user: TelegramUser = Depends(get_current_user),
) -> LessonContent:
    """Get a single lesson with content and exercises."""
    slug = f'{block_slug}/{lesson_slug}'
    try:
        return get_lesson(course, slug)
    except FileNotFoundError:
        raise HTTPException(status_code=404, detail=f'Lesson {slug} not found')
