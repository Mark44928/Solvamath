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
