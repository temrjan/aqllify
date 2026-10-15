"""Tests for SM-2 spaced repetition algorithm."""

from src.progress.service import get_next_title_info, get_title_for_xp, sm2_calculate


class TestSm2Algorithm:
    """SM-2 core algorithm tests."""

    def test_correct_first_time(self) -> None:
        ease, interval = sm2_calculate(
            quality=4, ease_factor=2.5, interval_days=0, correct_count=0
        )
        assert interval == 1
        assert ease >= 2.5

    def test_correct_second_time(self) -> None:
        _ease, interval = sm2_calculate(
            quality=4, ease_factor=2.5, interval_days=1, correct_count=1
        )
        assert interval == 3

    def test_correct_third_time(self) -> None:
        _ease, interval = sm2_calculate(
            quality=4, ease_factor=2.5, interval_days=3, correct_count=2
        )
        assert interval == round(3 * 2.5)  # ~8 days

    def test_incorrect_resets_interval(self) -> None:
        _ease, interval = sm2_calculate(
            quality=1, ease_factor=2.5, interval_days=14, correct_count=5
        )
        assert interval == 1  # Reset to 1 day

    def test_easy_increases_ease(self) -> None:
        ease, _ = sm2_calculate(
            quality=5, ease_factor=2.5, interval_days=1, correct_count=1
        )
        assert ease > 2.5

    def test_hard_decreases_ease(self) -> None:
        ease, _ = sm2_calculate(
            quality=3, ease_factor=2.5, interval_days=1, correct_count=1
        )
        assert ease < 2.5

    def test_ease_never_below_minimum(self) -> None:
        ease, _ = sm2_calculate(
            quality=0, ease_factor=1.3, interval_days=1, correct_count=1
        )
        assert ease >= 1.3


class TestTitles:
    """Title system tests."""

    def test_initial_title(self) -> None:
        assert get_title_for_xp(0) == "spark"

    def test_pulse_at_500(self) -> None:
        assert get_title_for_xp(500) == "pulse"

    def test_apex_at_50000(self) -> None:
        assert get_title_for_xp(50000) == "apex"

    def test_storm_at_6000(self) -> None:
        assert get_title_for_xp(6000) == "storm"

    def test_between_levels(self) -> None:
        assert get_title_for_xp(2000) == "wave"  # 1500-3000

    def test_next_title_from_zero(self) -> None:
        name, xp_needed = get_next_title_info(0)
        assert name == "pulse"
        assert xp_needed == 500

    def test_next_title_from_apex(self) -> None:
        name, xp_needed = get_next_title_info(50000)
        assert name is None
        assert xp_needed == 0

    def test_next_title_mid_level(self) -> None:
        name, xp_needed = get_next_title_info(4000)
        assert name == "storm"
        assert xp_needed == 2000
