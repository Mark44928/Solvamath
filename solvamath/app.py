"""Textual application shell for Solvamath."""

from __future__ import annotations

from textual.app import App

from .game import Game
from .screens import GameScreen, MenuScreen
from .storage import Store
from .theme import Palette, get_palette, next_theme


class SolvamathApp(App[None]):
    CSS_PATH = "styles.tcss"
    TITLE = "Solvamath"
    SUB_TITLE = "math puzzles for the terminal"
    ENABLE_COMMAND_PALETTE = False
    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(
        self,
        store: Store | None = None,
        start_mode: str | None = None,
        seed: int | None = None,
    ) -> None:
        super().__init__()
        self.store = store or Store()
        self.palette: Palette = get_palette(self.store.settings.theme)
        self.start_mode = start_mode
        self.seed = seed

    def on_mount(self) -> None:
        self.push_screen(MenuScreen(auto_start=self.start_mode))

    def start_game(self, mode: str) -> None:
        self.switch_screen(GameScreen(Game(mode, self.store.settings.difficulty, self.seed)))

    def set_difficulty(self, key: str) -> None:
        self.store.update_settings(difficulty=key)

    def cycle_theme(self) -> None:
        key = next_theme(self.store.settings.theme)
        self.store.update_settings(theme=key)
        self.palette = get_palette(key)
