"""Content validation tests — catch broken lessons before deploy."""

import pytest

from src.lessons.service import list_lessons, get_lesson

COURSE = "uzlearn"

VALID_EXERCISE_TYPES = {
    "open_translate",
    "reverse_translate",
    "fill_blank",
    "build_sentence",
    "choice",
    "listen_write",
    "dialog_reply",
    "context_use",
    "spiral",
}


def get_all_lessons():
    """Load all lessons for parametrized tests."""
    items = list_lessons(COURSE)
    return [(item.slug, get_lesson(COURSE, item.slug)) for item in items]


ALL_LESSONS = get_all_lessons()
# Checkpoint lessons have no phrases/exercises/grammar — they use AI dialog
REGULAR_LESSONS = [(s, lesson) for s, lesson in ALL_LESSONS if "checkpoint" not in s]


class TestAllLessonsStructure:
    """Every lesson must have required fields and valid content."""

    @pytest.mark.parametrize(
        "slug,lesson", ALL_LESSONS, ids=[s for s, _ in ALL_LESSONS]
    )
    def test_meta_fields(self, slug, lesson):
        assert lesson.meta.title, f"{slug}: empty title"
        assert lesson.meta.block >= 1, f"{slug}: invalid block"
        assert lesson.meta.lesson >= 1, f"{slug}: invalid lesson"
        assert lesson.meta.xp_reward > 0, f"{slug}: no xp_reward"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_has_phrases(self, slug, lesson):
        assert len(lesson.phrases) >= 3, f"{slug}: less than 3 phrases"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_phrases_have_cyrillic(self, slug, lesson):
        for i, phrase in enumerate(lesson.phrases):
            assert phrase.uzbek, f"{slug}: phrase {i} empty uzbek"
            assert phrase.russian, f"{slug}: phrase {i} empty russian"
            assert phrase.uzbek_cyrillic, f"{slug}: phrase {i} missing uzbek_cyrillic"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_has_exercises(self, slug, lesson):
        assert len(lesson.exercises) >= 5, f"{slug}: less than 5 exercises"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_exercise_types_valid(self, slug, lesson):
        for i, ex in enumerate(lesson.exercises):
            assert ex.type in VALID_EXERCISE_TYPES, (
                f'{slug}: exercise {i} has unknown type "{ex.type}"'
            )

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_exercises_have_content(self, slug, lesson):
        for i, ex in enumerate(lesson.exercises):
            if ex.type == "dialog_reply":
                assert ex.context, f"{slug}: exercise {i} dialog_reply missing context"
                assert ex.bot_says, (
                    f"{slug}: exercise {i} dialog_reply missing bot_says"
                )
                assert ex.answer_context, (
                    f"{slug}: exercise {i} dialog_reply missing answer_context"
                )
            elif ex.type == "choice":
                assert ex.prompt, f"{slug}: exercise {i} choice missing prompt"
                assert ex.options and len(ex.options) >= 2, (
                    f"{slug}: exercise {i} choice needs >=2 options"
                )
                assert ex.correct is not None, (
                    f"{slug}: exercise {i} choice missing correct index"
                )
                assert 0 <= ex.correct < len(ex.options), (
                    f"{slug}: exercise {i} correct index out of range"
                )
            elif ex.type == "build_sentence":
                assert ex.prompt, f"{slug}: exercise {i} build_sentence missing prompt"
                assert ex.words and len(ex.words) >= 2, (
                    f"{slug}: exercise {i} build_sentence needs >=2 words"
                )
                assert ex.answer, f"{slug}: exercise {i} build_sentence missing answer"
            elif ex.type == "fill_blank":
                assert ex.prompt, f"{slug}: exercise {i} fill_blank missing prompt"
                assert "___" in ex.prompt, (
                    f"{slug}: exercise {i} fill_blank prompt has no ___"
                )
                assert ex.answer, f"{slug}: exercise {i} fill_blank missing answer"
            else:
                assert ex.prompt, f"{slug}: exercise {i} ({ex.type}) missing prompt"
                assert ex.answer_context or ex.answer, (
                    f"{slug}: exercise {i} ({ex.type}) missing answer_context and answer"
                )

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_has_grammar(self, slug, lesson):
        assert len(lesson.grammar) >= 1, f"{slug}: no grammar tips"
        for tip in lesson.grammar:
            assert "**" not in tip.text, f"{slug}: markdown in grammar"
            assert "##" not in tip.text, f"{slug}: heading in grammar"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_xp_positive(self, slug, lesson):
        for i, ex in enumerate(lesson.exercises):
            assert ex.xp > 0, f"{slug}: exercise {i} has 0 xp"


class TestExerciseTypeMix:
    """Lessons should have a mix of exercise types, not all the same."""

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_at_least_2_types(self, slug, lesson):
        types = {ex.type for ex in lesson.exercises}
        assert len(types) >= 2, f"{slug}: only 1 exercise type ({types}), need variety"

    @pytest.mark.parametrize(
        "slug,lesson", REGULAR_LESSONS, ids=[s for s, _ in REGULAR_LESSONS]
    )
    def test_not_all_choice(self, slug, lesson):
        choice_count = sum(1 for ex in lesson.exercises if ex.type == "choice")
        total = len(lesson.exercises)
        assert choice_count < total * 0.5, (
            f"{slug}: {choice_count}/{total} exercises are choice — too many"
        )
