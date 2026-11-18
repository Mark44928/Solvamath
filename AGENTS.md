# AGENTS.md — Solvamath

Terminal math puzzle game built with Python + Textual. Keep the game core pure
Python; Textual only renders and routes input.

## Rules

- Python 3.10+, standard library only at runtime except **Textual**.
- `solvamath/puzzles.py` and `solvamath/game.py` must not import Textual.
- Never use `eval()` or `exec()`. User expressions go through
  `safe_eval_expression()`, a small AST whitelist.
- Puzzle answers and persisted JSON are untrusted input: keep the current
  bounds and numeric sanitization.
- Persistence is atomic (`tmp.replace`) and must never crash on bad state.
- Keep the game playable at 80×24 and usable with a keyboard only.
- Every new puzzle family needs a deterministic generator test and an answer
  check test. Every scoring/life/streak change needs a game test.
- `make check` must stay green.
- Do not commit generated caches, virtualenvs or the user's saved state.
- Commit style: short imperative subject.

## Map

| Path | Role |
|---|---|
| `solvamath/models.py` | Data classes, modes and difficulties |
| `solvamath/puzzles.py` | Generators + safe answer checking |
| `solvamath/game.py` | Run state, timer, scoring, hints |
| `solvamath/storage.py` | Settings, profile and top scores |
| `solvamath/theme.py` | Theme palettes |
| `solvamath/screens.py` | Menu, game, results, stats, help |
| `solvamath/app.py` | Textual app shell |
| `tests/` | Pure-core and headless UI tests |
