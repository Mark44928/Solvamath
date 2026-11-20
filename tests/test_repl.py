from __future__ import annotations

from pathlib import Path

import solvamath.__main__ as cli
from solvamath.models import Puzzle
from solvamath.storage import Store

PUZZLE = Puzzle(
    "missing_number",
    "Missing number",
    "5 x ? = 15",
    "3",
    "Divide 15 by 5.",
    "3",
)


def test_repl_is_puzzle_practice_not_a_calculator(tmp_path: Path, monkeypatch, capsys) -> None:
    store = Store(tmp_path / "state.json")
    answers = iter(["2+3*4", "hint", "3", "quit"])
    monkeypatch.setattr(cli, "make_puzzle", lambda _rng, _difficulty: PUZZLE)
    monkeypatch.setattr(cli, "check_answer", lambda puzzle, line: line == puzzle.answer)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    assert cli.run_repl(store) == 0
    out = capsys.readouterr().out
    assert "not quite" in out
    assert "hint: Divide 15 by 5." in out
    assert "correct — next puzzle" in out
    assert "session: 1 solved / 2 attempts" in out


def test_repl_persists_theme_and_skips(tmp_path: Path, monkeypatch, capsys) -> None:
    store = Store(tmp_path / "state.json")
    answers = iter(["theme bluney", "theme nope", "skip", "quit"])
    monkeypatch.setattr(cli, "make_puzzle", lambda _rng, _difficulty: PUZZLE)
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    assert cli.run_repl(store) == 0
    out = capsys.readouterr().out
    assert "theme: bluney" in out
    assert "unknown theme: nope" in out
    assert "answer: 3" in out
    assert store.settings.theme == "bluney"
