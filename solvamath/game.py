"""Game rules and scoring. Pure Python; no Textual imports."""

from __future__ import annotations

import random
import secrets
from collections import Counter

from .models import DIFFICULTIES, MODES, Outcome, Puzzle
from .puzzles import check_answer, daily_seed, make_puzzle

KIND_BONUS = {
    "equation": 1.0,
    "missing_number": 0.9,
    "sequence": 1.05,
    "true_false": 0.8,
    "operators": 1.35,
    "prime": 0.95,
    "target": 1.6,
}


class Game:
    def __init__(
        self,
        mode_key: str = "campaign",
        difficulty_key: str = "normal",
        seed: int | None = None,
    ) -> None:
        self.mode = MODES.get(mode_key, MODES["campaign"])
        self.difficulty = DIFFICULTIES.get(difficulty_key, DIFFICULTIES["normal"])
        if self.mode.key == "daily":
            self.seed = daily_seed()
        else:
            self.seed = seed if seed is not None else secrets.randbits(32)
        self.rng = random.Random(self.seed)
        self.score = 0
        self.solved = 0
        self.attempts = 0
        self.streak = 0
        self.best_streak = 0
        self.lives = 999 if self.mode.key == "zen" else min(self.mode.lives, self.difficulty.lives)
        self.max_lives = self.lives
        self.round_no = 1
        self.time_left = self.difficulty.time_limit if self.mode.timed else 0
        self.awaiting_next = False
        self.finished = False
        self.hint_used = False
        self.solved_kinds: Counter[str] = Counter()
        self.puzzle = self._next_puzzle()

    def _next_puzzle(self) -> Puzzle:
        return make_puzzle(self.rng, self.difficulty.key)

    @property
    def round_limit(self) -> int:
        return self.mode.rounds

    @property
    def time_ratio(self) -> float:
        if not self.mode.timed:
            return 1.0
        return max(0.0, min(1.0, self.time_left / max(1, self.difficulty.time_limit)))

    @property
    def accuracy(self) -> float:
        return self.solved / self.attempts if self.attempts else 0.0

    def use_hint(self) -> str:
        if self.finished or self.awaiting_next:
            return ""
        self.hint_used = True
        self.score = max(0, self.score - max(5, self.difficulty.points // 4))
        return self.puzzle.hint

    def submit(self, answer: str) -> Outcome:
        if self.finished or self.awaiting_next:
            return self._locked_outcome()
        correct = check_answer(self.puzzle, answer)
        return self._record(correct, timed_out=False)

    def timeout(self) -> Outcome:
        if self.finished or self.awaiting_next:
            return self._locked_outcome()
        return self._record(False, timed_out=True)

    def tick(self, seconds: int = 1) -> Outcome | None:
        if self.finished or self.awaiting_next or not self.mode.timed:
            return None
        self.time_left = max(0, self.time_left - max(1, seconds))
        if self.time_left == 0:
            return self.timeout()
        return None

    def _record(self, correct: bool, timed_out: bool) -> Outcome:
        self.attempts += 1
        self.awaiting_next = True
        if correct:
            self.solved += 1
            self.streak += 1
            self.best_streak = max(self.best_streak, self.streak)
            self.solved_kinds[self.puzzle.kind] += 1
            base = int(self.difficulty.points * KIND_BONUS.get(self.puzzle.kind, 1.0))
            if self.mode.timed:
                base += int(self.time_left * 1.5)
            if self.hint_used:
                base //= 2
            points = max(10, base) * min(5, 1 + self.streak // 2)
            self.score += points
            message = f"Correct. +{points} points."
        else:
            self.streak = 0
            points = 0
            self.lives -= 1
            message = "Time." if timed_out else "Not quite."
        self.finished = self.lives <= 0 or self.round_no >= self.round_limit
        return Outcome(
            correct=correct,
            timed_out=timed_out,
            points=points,
            message=message,
            solution=self.puzzle.solution,
            finished=self.finished,
            score=self.score,
            streak=self.streak,
            lives=self.lives,
        )

    def advance(self) -> bool:
        if self.finished:
            return False
        self.round_no += 1
        self.awaiting_next = False
        self.hint_used = False
        self.time_left = self.difficulty.time_limit if self.mode.timed else 0
        self.puzzle = self._next_puzzle()
        return True

    def _locked_outcome(self) -> Outcome:
        return Outcome(
            correct=False,
            timed_out=False,
            points=0,
            message="Waiting for the next puzzle.",
            solution=self.puzzle.solution,
            finished=self.finished,
            score=self.score,
            streak=self.streak,
            lives=self.lives,
        )
