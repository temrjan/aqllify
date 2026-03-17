import json
import re
from pathlib import Path

import yaml

from src.lessons.schemas import (
    Exercise,
    GrammarTip,
    Homework,
    LessonContent,
    LessonListItem,
    LessonMeta,
    MiniDialog,
    Phrase,
)

COURSES_DIR = Path(__file__).parent.parent.parent.parent / "courses"


def get_course_path(course: str) -> Path:
    path = COURSES_DIR / course
    if not path.exists():
        raise FileNotFoundError(f"Course not found: {course}")
    return path


def list_lessons(course: str) -> list[LessonListItem]:
    """List all lessons in a course, sorted by block/lesson number."""
    course_path = get_course_path(course)
    lessons: list[LessonListItem] = []

    for block_dir in sorted(course_path.iterdir()):
        if not block_dir.is_dir() or block_dir.name.startswith("."):
            continue

        for lesson_dir in sorted(block_dir.iterdir()):
            if not lesson_dir.is_dir():
                continue

            lesson_md = lesson_dir / "lesson.md"
            if not lesson_md.exists():
                continue

            meta = _parse_frontmatter(lesson_md)
            slug = f"{block_dir.name}/{lesson_dir.name}"

            lessons.append(
                LessonListItem(
                    slug=slug,
                    title=meta.title,
                    block=meta.block,
                    lesson=meta.lesson,
                )
            )

    lessons.sort(key=lambda x: (x.block, x.lesson))
    return lessons


def get_lesson(course: str, slug: str) -> LessonContent:
    """Load a single lesson with content and exercises."""
    course_path = get_course_path(course)
    lesson_dir = course_path / slug

    if not lesson_dir.exists():
        raise FileNotFoundError(f"Lesson not found: {slug}")

    lesson_md = lesson_dir / "lesson.md"
    exercises_json = lesson_dir / "exercises.json"

    meta = _parse_frontmatter(lesson_md)
    body = _parse_body(lesson_md)

    phrases = _extract_phrases(body)
    grammar = _extract_grammar(body)
    dialog = _extract_dialog(body)
    homework = _extract_homework(body)

    exercises: list[Exercise] = []
    if exercises_json.exists():
        data = json.loads(exercises_json.read_text(encoding="utf-8"))
        exercises = [Exercise(**ex) for ex in data.get("exercises", [])]

    return LessonContent(
        meta=meta,
        slug=slug,
        phrases=phrases,
        grammar=grammar,
        dialog=dialog,
        homework=homework,
        exercises=exercises,
    )


def _parse_frontmatter(md_path: Path) -> LessonMeta:
    text = md_path.read_text(encoding="utf-8")
    if not text.startswith("---"):
        raise ValueError(f"No frontmatter in {md_path}")

    parts = text.split("---", 2)
    if len(parts) < 3:
        raise ValueError(f"Invalid frontmatter in {md_path}")

    front = yaml.safe_load(parts[1])
    return LessonMeta(**front)


def _parse_body(md_path: Path) -> str:
    text = md_path.read_text(encoding="utf-8")
    parts = text.split("---", 2)
    return parts[2].strip() if len(parts) >= 3 else text


def _clean_md(text: str) -> str:
    """Remove markdown formatting, return plain text."""
    text = re.sub(r"\*\*(.+?)\*\*", r"\1", text)  # **bold** → bold
    text = re.sub(r"\*(.+?)\*", r"\1", text)  # *italic* → italic
    text = re.sub(r"^#+\s+", "", text, flags=re.MULTILINE)  # ## heading → heading
    text = re.sub(r"^- ", "", text, flags=re.MULTILINE)  # - item → item
    text = re.sub(r"`(.+?)`", r"\1", text)  # `code` → code
    return text.strip()


def _extract_phrases(body: str) -> list[Phrase]:
    """Extract phrases from markdown table."""
    phrases: list[Phrase] = []
    in_table = False

    for line in body.split("\n"):
        stripped = line.strip()

        if stripped.startswith("|") and (
            "Узбекский" in stripped or "O'zbek" in stripped
        ):
            in_table = True
            continue

        if in_table and stripped.startswith("|---"):
            continue

        if in_table and stripped.startswith("|"):
            cells = [c.strip() for c in stripped.split("|")[1:-1]]
            if len(cells) >= 3:
                uzbek = cells[0].strip()
                uzbek_cyrillic = cells[1].strip()
                russian = cells[2].strip()
                if uzbek and russian:
                    phrases.append(
                        Phrase(
                            uzbek=uzbek, uzbek_cyrillic=uzbek_cyrillic, russian=russian
                        )
                    )
            elif len(cells) >= 2:
                uzbek = cells[0].strip()
                russian = cells[1].strip()
                if uzbek and russian:
                    phrases.append(Phrase(uzbek=uzbek, russian=russian))
        elif in_table and not stripped.startswith("|"):
            in_table = False

    return phrases


def _extract_section(body: str, header: str) -> str | None:
    """Extract text between a ## header and the next ## header."""
    pattern = rf"##\s+{re.escape(header)}.*?\n(.*?)(?=\n##\s|\Z)"
    match = re.search(pattern, body, re.DOTALL)
    if not match:
        return None
    return match.group(1).strip()


def _extract_grammar(body: str) -> list[GrammarTip]:
    """Extract grammar section as clean text paragraphs."""
    section = _extract_section(body, "Грамматика")
    if not section:
        return []

    tips: list[GrammarTip] = []
    current: list[str] = []

    for line in section.split("\n"):
        stripped = line.strip()
        if not stripped:
            if current:
                tips.append(GrammarTip(text=_clean_md("\n".join(current))))
                current = []
        else:
            current.append(stripped)

    if current:
        tips.append(GrammarTip(text=_clean_md("\n".join(current))))

    return tips


def _extract_dialog(body: str) -> MiniDialog | None:
    """Extract dialog section as list of lines."""
    section = _extract_section(body, "Мини-диалог")
    if not section:
        return None

    lines = [
        _clean_md(line.strip())
        for line in section.split("\n")
        if line.strip() and line.strip().startswith("—")
    ]

    return MiniDialog(lines=lines) if lines else None


def _extract_homework(body: str) -> Homework | None:
    """Extract homework section as plain text."""
    section = _extract_section(body, "Задание на дом")
    if not section:
        return None
    return Homework(text=_clean_md(section))
