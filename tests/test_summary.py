from __future__ import annotations

from solvamath.storage import Profile, ScoreEntry
from solvamath.summary import accuracy_percent, mode_counts, recent_scores, sparkline


def entry(score: int, mode: str = "campaign", date: str = "2026-01-01") -> ScoreEntry:
    return ScoreEntry(score, mode, "normal", 5, 6, 3, date)


def test_accuracy_handles_empty_and_filled_profiles() -> None:
    assert accuracy_percent(Profile()) == 0.0
    assert accuracy_percent(Profile(solved=3, attempts=4)) == 75.0


def test_mode_counts_are_sorted_and_recent_scores_are_limited() -> None:
    scores = [
        entry(10, "zen", "2026-01-01"),
        entry(20, "campaign", "2026-01-03"),
        entry(30, "zen", "2026-01-02"),
        entry(40, "campaign", "2026-01-04"),
    ]
    assert mode_counts(scores) == [("campaign", 2), ("zen", 2)]
    assert recent_scores(scores, limit=3) == [30, 20, 40]


def test_sparkline_marks_low_and_high() -> None:
    assert sparkline([]) == ""
    assert sparkline([5, 5]) == "──"
    line = sparkline([1, 5, 10])
    assert line[0] == "▁"
    assert line[-1] == "█"
