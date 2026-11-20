"""Small derived views for the stats screen."""

from __future__ import annotations

from collections import Counter

from .storage import Profile, ScoreEntry


def accuracy_percent(profile: Profile) -> float:
    return profile.solved / profile.attempts * 100 if profile.attempts else 0.0


def mode_counts(scores: list[ScoreEntry]) -> list[tuple[str, int]]:
    counts = Counter(entry.mode for entry in scores)
    return sorted(counts.items())


def recent_scores(scores: list[ScoreEntry], limit: int = 8) -> list[int]:
    chronological = sorted(scores, key=lambda entry: entry.date)
    return [entry.score for entry in chronological[-limit:]]


def sparkline(values: list[int]) -> str:
    if not values:
        return ""
    low, high = min(values), max(values)
    if high == low:
        return "─" * len(values)
    blocks = "▁▂▃▄▅▆▇█"
    return "".join(blocks[round((value - low) / (high - low) * (len(blocks) - 1))] for value in values)
