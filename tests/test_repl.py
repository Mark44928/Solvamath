from __future__ import annotations

from pathlib import Path

from solvamath.__main__ import run_repl
from solvamath.storage import Store


def test_repl_evaluates_and_persists_theme(tmp_path: Path, monkeypatch, capsys) -> None:
    store = Store(tmp_path / "state.json")
    answers = iter(["2+3*4", "theme bluney", "theme nope", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    assert run_repl(store) == 0
    out = capsys.readouterr().out
    assert "= 14" in out
    assert "theme: bluney" in out
    assert "unknown theme: nope" in out
    assert store.settings.theme == "bluney"


def test_repl_handles_bad_expression(tmp_path: Path, monkeypatch, capsys) -> None:
    store = Store(tmp_path / "state.json")
    answers = iter(["2+", "quit"])
    monkeypatch.setattr("builtins.input", lambda _prompt="": next(answers))

    assert run_repl(store) == 0
    assert "error:" in capsys.readouterr().out
