"""Atomic local persistence for Solvamath."""

from __future__ import annotations

import contextlib
import json
import os
from dataclasses import asdict, dataclass, field
from datetime import date
from pathlib import Path
from typing import TYPE_CHECKING

from .models import DIFFICULTIES, MODES

if TYPE_CHECKING:
    from .game import Game

MAX_SCORES = 20
THEME_KEYS = ("greenit", "bluney", "yellen", "nord", "dracula", "gruvbox", "catppuccin", "tokyonight", "mono")


def default_data_dir() -> Path:
    override = os.environ.get("SOLVAMATH_DATA_DIR")
    if override:
        return Path(override).expanduser()
    xdg = os.environ.get("XDG_DATA_HOME")
    base = Path(xdg).expanduser() if xdg else Path.home() / ".local" / "share"
    return base / "solvamath"


@dataclass(slots=True)
class Settings:
    difficulty: str = "normal"
    theme: str = "greenit"

    def sanitized(self) -> Settings:
        return Settings(
            difficulty=self.difficulty if self.difficulty in DIFFICULTIES else "normal",
            theme=self.theme if self.theme in THEME_KEYS else "greenit",
        )


@dataclass(slots=True)
class ScoreEntry:
    score: int
    mode: str
    difficulty: str
    solved: int
    attempts: int
    best_streak: int
    date: str


@dataclass(slots=True)
class Profile:
    runs: int = 0
    solved: int = 0
    attempts: int = 0
    best_score: int = 0
    best_streak: int = 0
    kinds: dict[str, int] = field(default_factory=dict)


class Store:
    def __init__(self, path: Path | None = None) -> None:
        self.path = path or default_data_dir() / "state.json"
        self.settings = Settings()
        self.profile = Profile()
        self.scores: list[ScoreEntry] = []
        self.load()

    def load(self) -> None:
        try:
            raw = json.loads(self.path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return
        if not isinstance(raw, dict):
            return
        raw_settings = raw.get("settings")
        if isinstance(raw_settings, dict):
            with contextlib.suppress(TypeError, ValueError):
                self.settings = Settings(
                    difficulty=str(raw_settings.get("difficulty", "normal")),
                    theme=str(raw_settings.get("theme", "greenit")),
                ).sanitized()
        raw_profile = raw.get("profile")
        if isinstance(raw_profile, dict):
            self.profile = Profile(
                runs=self._count(raw_profile.get("runs")),
                solved=self._count(raw_profile.get("solved")),
                attempts=self._count(raw_profile.get("attempts")),
                best_score=self._count(raw_profile.get("best_score")),
                best_streak=self._count(raw_profile.get("best_streak")),
                kinds=self._kinds(raw_profile.get("kinds")),
            )
        raw_scores = raw.get("scores")
        if isinstance(raw_scores, list):
            entries: list[ScoreEntry] = []
            for item in raw_scores:
                if not isinstance(item, dict):
                    continue
                try:
                    entry = ScoreEntry(
                        score=self._count(item.get("score")),
                        mode=str(item.get("mode", "campaign")),
                        difficulty=str(item.get("difficulty", "normal")),
                        solved=self._count(item.get("solved")),
                        attempts=self._count(item.get("attempts")),
                        best_streak=self._count(item.get("best_streak")),
                        date=str(item.get("date", ""))[:10],
                    )
                except (TypeError, ValueError):
                    continue
                if entry.mode not in MODES or entry.difficulty not in DIFFICULTIES:
                    continue
                entries.append(entry)
            self.scores = sorted(entries, key=lambda entry: entry.score, reverse=True)[:MAX_SCORES]

    def save(self) -> None:
        payload = {
            "version": 1,
            "settings": asdict(self.settings),
            "profile": asdict(self.profile),
            "scores": [asdict(entry) for entry in self.scores],
        }
        try:
            self.path.parent.mkdir(parents=True, exist_ok=True)
            tmp = self.path.with_name(self.path.name + ".tmp")
            tmp.write_text(json.dumps(payload, indent=2), encoding="utf-8")
            tmp.replace(self.path)
        except OSError:
            pass

    def update_settings(self, **changes: object) -> None:
        values = asdict(self.settings)
        values.update({key: value for key, value in changes.items() if key in values})
        self.settings = Settings(**values).sanitized()
        self.save()

    def record_run(self, game: Game) -> bool:
        previous = max(
            (entry.score for entry in self.scores
             if entry.mode == game.mode.key and entry.difficulty == game.difficulty.key),
            default=0,
        )
        new_best = game.score > previous
        entry = ScoreEntry(
            score=game.score,
            mode=game.mode.key,
            difficulty=game.difficulty.key,
            solved=game.solved,
            attempts=game.attempts,
            best_streak=game.best_streak,
            date=date.today().isoformat(),
        )
        self.scores.append(entry)
        self.scores.sort(key=lambda item: item.score, reverse=True)
        del self.scores[MAX_SCORES:]
        self.profile.runs += 1
        self.profile.solved += game.solved
        self.profile.attempts += game.attempts
        self.profile.best_score = max(self.profile.best_score, game.score)
        self.profile.best_streak = max(self.profile.best_streak, game.best_streak)
        for kind, count in game.solved_kinds.items():
            self.profile.kinds[kind] = self.profile.kinds.get(kind, 0) + count
        self.save()
        return new_best

    def best_for(self, mode: str, difficulty: str) -> int:
        return max(
            (entry.score for entry in self.scores
             if entry.mode == mode and entry.difficulty == difficulty),
            default=0,
        )

    @staticmethod
    def _count(value: object) -> int:
        try:
            number = int(value)  # type: ignore[arg-type]
        except (TypeError, ValueError, OverflowError):
            return 0
        return max(0, min(1_000_000_000, number))

    @classmethod
    def _kinds(cls, value: object) -> dict[str, int]:
        if not isinstance(value, dict):
            return {}
        return {
            str(key)[:24]: cls._count(count)
            for key, count in value.items()
            if isinstance(key, str) and cls._count(count) > 0
        }
