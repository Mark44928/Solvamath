from __future__ import annotations

from pathlib import Path

from solvamath.app import SolvamathApp
from solvamath.screens import GameScreen, MenuScreen
from solvamath.storage import Store


async def test_menu_boots_at_80x24(tmp_path: Path) -> None:
    app = SolvamathApp(store=Store(tmp_path / "state.json"))
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen)
        assert app.screen.query_one("#start-campaign").display


async def test_menu_keybinds_t_and_x(tmp_path: Path) -> None:
    # t / x are advertised in the README and the menu hint; they must route to
    # cycle_theme / cycle_difficulty. Without a BINDINGS entry they did nothing.
    app = SolvamathApp(store=Store(tmp_path / "state.json"))
    async with app.run_test(size=(80, 24)) as pilot:
        await pilot.pause()
        before = app.store.settings.theme
        await pilot.press("t")
        await pilot.pause()
        assert app.store.settings.theme != before
        diff_before = app.store.settings.difficulty
        await pilot.press("x")
        await pilot.pause()
        assert app.store.settings.difficulty != diff_before


async def test_game_keybinds_h_and_k(tmp_path: Path) -> None:
    # H / K are advertised in the README and the game-hint line. They are
    # priority bindings, so they fire even while the answer Input is focused —
    # without priority, Input._on_key consumes printable keys as text input
    # and the keys silently typed into the box.
    app = SolvamathApp(store=Store(tmp_path / "state.json"))
    async with app.run_test(size=(80, 24)) as pilot:
        app.start_game("campaign")
        await pilot.pause()
        await pilot.pause()
        scr = app.screen
        assert isinstance(scr, GameScreen)
        answer = scr.query_one("#answer")
        answer.focus()
        await pilot.pause()
        await pilot.pause()
        # focused: H / K still fire the binding, they do not type into the box
        await pilot.press("h")
        await pilot.pause()
        await pilot.pause()
        assert answer.value == ""
        assert scr.game.hint_used is True
        before = scr.game.attempts
        await pilot.press("k")
        await pilot.pause()
        await pilot.pause()
        assert scr.game.attempts == before + 1


async def test_solution_form_accepted_for_every_puzzle(tmp_path: Path) -> None:
    # Every puzzle prints a human-readable solution ("x = 10", "next = 36",
    # "answer = 36") whose trailing value is the bare answer. Typing the
    # solution exactly as shown must be accepted, not rejected.
    import random

    from solvamath.puzzles import check_answer, make_puzzle

    rng = random.Random(7)
    kinds = set()
    for _ in range(200):
        p = make_puzzle(rng, "normal")
        if p.kind in ("target", "operators", "true_false"):
            continue
        kinds.add(p.kind)
        assert check_answer(p, p.solution), (p.kind, p.solution, p.answer)
        assert check_answer(p, p.answer)
    assert {"equation", "sequence", "missing_number", "prime"} <= kinds


async def test_menu_and_game_screen_boot(tmp_path: Path) -> None:
    app = SolvamathApp(store=Store(tmp_path / "state.json"))
    async with app.run_test(size=(100, 30)) as pilot:
        await pilot.pause()
        assert isinstance(app.screen, MenuScreen)
        app.start_game("campaign")
        await pilot.pause()
        assert isinstance(app.screen, GameScreen)
        screen = app.screen
        assert "LIVES 3/3" in str(screen.query_one("#status-line").render())
        screen.query_one("#answer").value = screen.game.puzzle.answer
        await pilot.press("enter")
        await pilot.pause()
        assert screen.game.attempts == 1
