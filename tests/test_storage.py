from __future__ import annotations

from pathlib import Path

from solvamath.achievements import achievements_for
from solvamath.game import Game
from solvamath.storage import ScoreEntry, Settings, Store


def test_store_round_trip_and_profile(tmp_path: Path) -> None:
    path = tmp_path / "state.json"
    store = Store(path)
    store.update_settings(difficulty="hard", theme="bluney")
    game = Game("campaign", "hard", seed=77)
    assert game.submit(game.puzzle.answer).correct
    assert store.record_run(game)
    loaded = Store(path)
    assert loaded.settings.difficulty == "hard"
    assert loaded.settings.theme == "bluney"
    assert loaded.profile.runs == 1
    assert loaded.profile.solved == 1
    assert loaded.scores[0].score == game.score


def test_store_sanitizes_bad_settings(tmp_path: Path) -> None:
    store = Store(tmp_path / "state.json")
    store.update_settings(difficulty="nonsense", theme="nonsense")
    loaded = Store(tmp_path / "state.json")
    assert loaded.settings == Settings("normal", "greenit")


def test_achievements_unlock_from_profile() -> None:
    store = Store(Path("/nonexistent/solvamath-test.json"))
    store.profile.solved = 12
    store.profile.best_streak = 10
    store.profile.kinds["target"] = 5
    store.scores = [
        ScoreEntry(5000, "campaign", "normal", 10, 10, 10, "2026-11-18")
    ]
    keys = {badge.key for badge in achievements_for(store.profile, store.scores)}
    assert {"first-steps", "ten-club", "hot-streak", "unstoppable", "perfect", "target-tamer", "grandmaster"} <= keys
