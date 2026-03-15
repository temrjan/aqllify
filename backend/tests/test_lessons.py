"""Tests for lesson content loading."""

from src.lessons.service import list_lessons, get_lesson


class TestLessonLoading:
    """Test that course content loads correctly."""

    def test_list_uzlearn_lessons(self) -> None:
        lessons = list_lessons('uzlearn')
        assert len(lessons) >= 1
        assert lessons[0].slug == 'block-1/01-salomlashish'
        assert lessons[0].block == 1
        assert lessons[0].lesson == 1

    def test_get_first_lesson(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert lesson.meta.title == 'Salomlashish (Приветствия)'
        assert lesson.meta.block == 1
        assert lesson.meta.lesson == 1
        assert lesson.meta.xp_reward == 50

    def test_lesson_has_phrases(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert len(lesson.phrases) == 5
        assert lesson.phrases[0].uzbek == 'Salom'
        assert lesson.phrases[0].russian == 'Привет'

    def test_lesson_has_exercises(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert len(lesson.exercises) == 10
        assert lesson.exercises[0].type == 'open_translate'

    def test_lesson_has_grammar(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert len(lesson.grammar) >= 1
        # No markdown symbols in grammar text
        for tip in lesson.grammar:
            assert '**' not in tip.text
            assert '##' not in tip.text

    def test_lesson_has_dialog(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert lesson.dialog is not None
        assert len(lesson.dialog.lines) >= 2

    def test_lesson_has_homework(self) -> None:
        lesson = get_lesson('uzlearn', 'block-1/01-salomlashish')
        assert lesson.homework is not None
        assert len(lesson.homework.text) > 0

    def test_nonexistent_course_raises(self) -> None:
        try:
            list_lessons('nonexistent')
            assert False, 'Should have raised FileNotFoundError'
        except FileNotFoundError:
            pass

    def test_nonexistent_lesson_raises(self) -> None:
        try:
            get_lesson('uzlearn', 'block-99/99-fake')
            assert False, 'Should have raised FileNotFoundError'
        except FileNotFoundError:
            pass
