"""Achievements derived from persisted play statistics."""

from __future__ import annotations

from dataclasses import dataclass

from .storage import Profile, ScoreEntry


@dataclass(frozen=True, slots=True)
class Achievement:
    key: str
    title: str
    detail: str


def achievements_for(profile: Profile, scores: list[ScoreEntry]) -> list[Achievement]:
    earned: list[Achievement] = []
    best_score = max(profile.best_score, max((entry.score for entry in scores), default=0))

    def add(key: str, title: str, detail: str, condition: bool) -> None:
        if condition:
            earned.append(Achievement(key, title, detail))

    add("first-steps", "FIRST STEPS", "solve your first puzzle", profile.solved >= 1)
    add("ten-club", "TEN CLUB", "solve 10 puzzles", profile.solved >= 10)
    add("fifty", "HALF CENTURY", "solve 50 puzzles", profile.solved >= 50)
    add("hot-streak", "HOT STREAK", "reach a 5 answer streak", profile.best_streak >= 5)
    add("unstoppable", "UNSTOPPABLE", "reach a 10 answer streak", profile.best_streak >= 10)
    add("perfect", "FLAWLESS", "finish a run with every answer correct",
        any(entry.attempts >= 10 and entry.solved == entry.attempts for entry in scores))
    add("target-tamer", "TARGET TAMER", "solve 5 Make 24 puzzles", profile.kinds.get("target", 0) >= 5)
    add("daily-habit", "DAILY HABIT", "play the Daily on 5 different days",
        len({entry.date for entry in scores if entry.mode == "daily"}) >= 5)
    add("grandmaster", "GRANDMASTER", "score 5000 in one run", best_score >= 5000)
    add("marathon", "MARATHON", "play 20 runs", profile.runs >= 20)
    return earned
