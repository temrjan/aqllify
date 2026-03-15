import json
from pathlib import Path

import markdown
import yaml

from src.lessons.schemas import Exercise, LessonContent, LessonListItem, LessonMeta, Phrase

COURSES_DIR = Path(__file__).parent.parent.parent.parent / 'courses'


def get_course_path(course: str) -> Path:
    path = COURSES_DIR / course
    if not path.exists():
        raise FileNotFoundError(f'Course not found: {course}')
    return path


def list_lessons(course: str) -> list[LessonListItem]:
    """List all lessons in a course, sorted by block/lesson number."""
    course_path = get_course_path(course)
    lessons: list[LessonListItem] = []

    for block_dir in sorted(course_path.iterdir()):
        if not block_dir.is_dir() or block_dir.name.startswith('.'):
            continue

        for lesson_dir in sorted(block_dir.iterdir()):
            if not lesson_dir.is_dir():
                continue

            lesson_md = lesson_dir / 'lesson.md'
            if not lesson_md.exists():
                continue

            meta = _parse_frontmatter(lesson_md)
            slug = f'{block_dir.name}/{lesson_dir.name}'

            lessons.append(LessonListItem(
                slug=slug,
                title=meta.title,
                block=meta.block,
                lesson=meta.lesson,
            ))

    lessons.sort(key=lambda x: (x.block, x.lesson))
    return lessons


def get_lesson(course: str, slug: str) -> LessonContent:
    """Load a single lesson with content and exercises."""
    course_path = get_course_path(course)
    lesson_dir = course_path / slug

    if not lesson_dir.exists():
        raise FileNotFoundError(f'Lesson not found: {slug}')

    lesson_md = lesson_dir / 'lesson.md'
    exercises_json = lesson_dir / 'exercises.json'

    # Parse frontmatter + body
    meta = _parse_frontmatter(lesson_md)
    body = _parse_body(lesson_md)
    body_html = markdown.markdown(body, extensions=['tables'])

    # Parse phrases from markdown table
    phrases = _extract_phrases(body)

    # Load exercises
    exercises: list[Exercise] = []
    if exercises_json.exists():
        data = json.loads(exercises_json.read_text(encoding='utf-8'))
        exercises = [Exercise(**ex) for ex in data.get('exercises', [])]

    return LessonContent(
        meta=meta,
        slug=slug,
        body_html=body_html,
        phrases=phrases,
        exercises=exercises,
    )


def _parse_frontmatter(md_path: Path) -> LessonMeta:
    """Extract YAML frontmatter from markdown file."""
    text = md_path.read_text(encoding='utf-8')
    if not text.startswith('---'):
        raise ValueError(f'No frontmatter in {md_path}')

    parts = text.split('---', 2)
    if len(parts) < 3:
        raise ValueError(f'Invalid frontmatter in {md_path}')

    front = yaml.safe_load(parts[1])
    return LessonMeta(**front)


def _parse_body(md_path: Path) -> str:
    """Extract body (after frontmatter) from markdown file."""
    text = md_path.read_text(encoding='utf-8')
    parts = text.split('---', 2)
    return parts[2].strip() if len(parts) >= 3 else text


def _extract_phrases(body: str) -> list[Phrase]:
    """Extract phrases from markdown table (| Узбекский | Русский | format)."""
    phrases: list[Phrase] = []
    in_table = False

    for line in body.split('\n'):
        stripped = line.strip()

        if stripped.startswith('|') and ('Узбекский' in stripped or 'O\'zbek' in stripped):
            in_table = True
            continue

        if in_table and stripped.startswith('|---'):
            continue

        if in_table and stripped.startswith('|'):
            cells = [c.strip() for c in stripped.split('|')[1:-1]]
            if len(cells) >= 2:
                uzbek = cells[0].strip()
                russian = cells[1].strip()
                if uzbek and russian:
                    phrases.append(Phrase(uzbek=uzbek, russian=russian))
        elif in_table and not stripped.startswith('|'):
            in_table = False

    return phrases
