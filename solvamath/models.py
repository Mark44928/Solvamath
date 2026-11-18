"""Pure data models for Solvamath."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import date


@dataclass(frozen=True, slots=True)
class Difficulty:
    key: str
    label: str
    time_limit: int
    rounds: int
    lives: int
    points: int
    kinds: tuple[str, ...]


DIFFICULTIES = {
    "easy": Difficulty(
        "easy", "Easy", 60, 10, 3, 80,
        ("equation", "missing_number", "sequence", "true_false"),
    ),
    "normal": Difficulty(
        "normal", "Normal", 45, 10, 3, 120,
        ("equation", "missing_number", "sequence", "true_false", "operators", "prime"),
    ),
    "hard": Difficulty(
        "hard", "Hard", 35, 10, 3, 170,
        ("equation", "operators", "sequence", "target", "prime"),
    ),
    "expert": Difficulty(
        "expert", "Expert", 25, 12, 2, 240,
        ("operators", "target", "equation", "sequence", "prime"),
    ),
}
DIFFICULTY_ORDER = ("easy", "normal", "hard", "expert")


@dataclass(frozen=True, slots=True)
class Mode:
    key: str
    label: str
    blurb: str
    rounds: int
    lives: int
    timed: bool


MODES = {
    "campaign": Mode("campaign", "Campaign", "10 puzzles, three lives", 10, 3, True),
    "daily": Mode("daily", "Daily", "the same run for everyone today", 10, 3, True),
    "endless": Mode("endless", "Endless", "keep going until the lives run out", 999, 3, True),
    "zen": Mode("zen", "Zen", "10 puzzles, no timer, no death", 10, 999, False),
}
MODE_ORDER = ("campaign", "daily", "endless", "zen")


@dataclass(frozen=True, slots=True)
class Puzzle:
    kind: str
    title: str
    prompt: str
    answer: str
    hint: str
    solution: str
    numbers: tuple[int, ...] = ()
    target: int | None = None


@dataclass(frozen=True, slots=True)
class Outcome:
    correct: bool
    timed_out: bool
    points: int
    message: str
    solution: str
    finished: bool
    score: int
    streak: int
    lives: int


@dataclass(slots=True)
class RunState:
    mode_key: str
    difficulty_key: str
    seed: int
    score: int = 0
    solved: int = 0
    attempts: int = 0
    streak: int = 0
    best_streak: int = 0
    lives: int = 3
    round_no: int = 1
    time_left: int = 0
    hint_used: bool = False
    awaiting_next: bool = False
    finished: bool = False
    started: str = field(default_factory=lambda: date.today().isoformat())
