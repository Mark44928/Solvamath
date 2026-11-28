"""Textual screens for Solvamath."""

from __future__ import annotations

from rich.text import Text
from textual.app import ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical, VerticalScroll
from textual.css.query import NoMatches
from textual.screen import Screen
from textual.widgets import Button, DataTable, Input, ProgressBar, Static

from .achievements import achievements_for
from .game import Game
from .models import DIFFICULTIES, Outcome
from .summary import accuracy_percent, mode_counts, recent_scores, sparkline

LOGO = (
    "  █▀ █▀█ █░░ █░█ █▀█ █▀▄▀█ █▀█ ▀█▀ █░█\n"
    "  ▄█ █▄█ █▄▄ ▀▄▀ █▀█ █░▀░█ █▀█ ░█░ █▀█"
)
PLACEHOLDERS = {
    "operators": "operators, e.g. +*",
    "true_false": "y or n",
    "target": "expression, e.g. (6+6)*(8-4)",
}


class ThemedScreen(Screen):
    def paint_palette(self) -> None:
        palette = self.app.palette
        self.styles.background = palette.bg
        for button in self.query(Button):
            button.styles.background = palette.panel
            button.styles.color = palette.text
            button.styles.border = ("round", palette.accent)
        for selector in ("#puzzle-card", "#result-card", "#stats-card", "#help-card"):
            try:
                widget = self.query_one(selector)
            except NoMatches:
                continue
            widget.styles.background = palette.panel
            widget.styles.border = ("round", palette.accent)
        for answer in self.query(Input):
            answer.styles.border = ("tall", palette.accent)


class MenuScreen(ThemedScreen):
    BINDINGS = [
        Binding("c", "start('campaign')", "Campaign"),
        Binding("d", "start('daily')", "Daily"),
        Binding("e", "start('endless')", "Endless"),
        Binding("z", "start('zen')", "Zen"),
        Binding("t", "cycle_theme", "Theme"),
        Binding("x", "cycle_difficulty", "Difficulty"),
        Binding("s", "stats", "Stats"),
        Binding("h", "help", "Help"),
    ]

    # t / x are wired through BINDINGS above (the README and the menu hint
    # advertise them). Without a binding entry Textual routes nothing to
    # action_cycle_theme / action_cycle_difficulty, so the keys did nothing.

    def __init__(self, auto_start: str | None = None) -> None:
        super().__init__()
        self.auto_start = auto_start

    def compose(self) -> ComposeResult:
        palette = self.app.palette
        profile = self.app.store.profile
        best = profile.best_score
        yield VerticalScroll(
            Vertical(
                Static(Text(LOGO, style=f"bold {palette.accent}"), id="logo"),
                Static(
                    Text(
                        "MATH PUZZLES · ONE DESK · NO MERCY",
                        style=f"bold {palette.accent2}",
                    ),
                    id="tagline",
                ),
                Static(
                    Text(
                        f"RUNS {profile.runs}   SOLVED {profile.solved}   BEST {best}",
                        style=palette.gold,
                    ),
                    id="profile-line",
                ),
                Static("CHOOSE A RUN", id="section-label"),
                Vertical(
                    Button("CAMPAIGN · three lives", id="start-campaign", classes="mode"),
                    Button("DAILY · shared seed", id="start-daily", classes="mode"),
                    Button("ENDLESS · one life run", id="start-endless", classes="mode"),
                    Button("ZEN · no timer", id="start-zen", classes="mode"),
                    id="mode-grid",
                ),
                Horizontal(
                    Button(
                        f"DIFF · {DIFFICULTIES[self.app.store.settings.difficulty].label.upper()}",
                        id="difficulty",
                    ),
                    Button(f"THEME · {palette.label.upper()}", id="theme"),
                    Button("STATS [S]", id="stats"),
                    Button("HELP [H]", id="help"),
                    id="utility-row",
                ),
                Static(
                    "ENTER choose · T theme · X difficulty · CTRL+Q quit",
                    id="menu-hint",
                ),
                id="menu",
            ),
            classes="screen-scroll",
        )

    def on_mount(self) -> None:
        self.paint_palette()
        if self.auto_start:
            self.call_after_refresh(self.app.start_game, self.auto_start)

    def on_button_pressed(self, event: Button.Pressed) -> None:
        button_id = event.button.id or ""
        if button_id.startswith("start-"):
            self.app.start_game(button_id.removeprefix("start-"))
        elif button_id == "difficulty":
            self.action_cycle_difficulty()
        elif button_id == "theme":
            self.action_cycle_theme()
        elif button_id == "stats":
            self.action_stats()
        elif button_id == "help":
            self.action_help()

    def action_start(self, mode: str) -> None:
        self.app.start_game(mode)

    def action_cycle_difficulty(self) -> None:
        order = ("easy", "normal", "hard", "expert")
        current = self.app.store.settings.difficulty
        next_key = order[(order.index(current) + 1) % len(order)]
        self.app.set_difficulty(next_key)
        self.app.switch_screen(MenuScreen())

    def action_cycle_theme(self) -> None:
        self.app.cycle_theme()
        self.app.switch_screen(MenuScreen())

    def action_stats(self) -> None:
        self.app.push_screen(StatsScreen())

    def action_help(self) -> None:
        self.app.push_screen(HelpScreen())


# The answer box is an Input, and Input.check_consume_key returns True for
# every printable character — so the screen's binding chain strips H / K
# from the bindings map before the app ever sees them, and the keys type
# into the box instead of firing the hint/skip. This subclass refuses to
# consume the game's own shortcut keys, so the screen binding survives and
# fires even while the box is focused.
SHORTCUT_KEYS = frozenset(("h", "k", "t", "x"))


class AnswerInput(Input):
    def check_consume_key(self, key: str, character: str | None) -> bool:
        if key in SHORTCUT_KEYS:
            return False
        return super().check_consume_key(key, character)


class GameScreen(ThemedScreen):
    BINDINGS = [
        Binding("escape", "menu", "Menu", priority=True),
        Binding("h", "hint", "Hint", priority=True),
        Binding("k", "skip", "Skip", priority=True),
    ]

    # H / K are advertised in the README and the game-hint line. They fire
    # even while the answer box is focused: AnswerInput refuses to consume
    # them, so the screen binding survives the binding chain and the app runs
    # it before forwarding the key to the box. Without this the keys silently
    # typed into the box.

    def __init__(self, game: Game) -> None:
        super().__init__()
        self.game = game
        self._waiting = False

    def compose(self) -> ComposeResult:
        yield VerticalScroll(
            Vertical(
                Static(id="game-title"),
                Static(id="status-line"),
                ProgressBar(total=100, show_eta=False, show_percentage=False, id="timer"),
                Vertical(
                    Static(id="puzzle-kind"),
                    Static(id="puzzle-prompt"),
                    AnswerInput(id="answer", placeholder="answer", max_length=80),
                    id="puzzle-card",
                ),
                Static(id="feedback"),
                Horizontal(
                    Button("HINT [H]", id="hint"),
                    Button("SKIP [K]", id="skip"),
                    Button("MENU [ESC]", id="to-menu"),
                    id="game-actions",
                ),
                Static(
                    "ENTER check · H hint · K skip · ESC menu",
                    id="game-hint",
                ),
                id="game",
            ),
            classes="screen-scroll",
        )

    def on_mount(self) -> None:
        self.paint_palette()
        self._refresh_view()
        if self.game.mode.timed:
            self.set_interval(1.0, self._tick)
        else:
            self.query_one("#timer", ProgressBar).display = False
        self.query_one("#answer", Input).focus()

    def _refresh_view(self) -> None:
        palette = self.app.palette
        game = self.game
        lives = "ZEN" if game.mode.key == "zen" else f"{max(0, game.lives)}/{game.max_lives}"
        title = Text()
        title.append("SOLVAMATH ", style=f"bold {palette.accent}")
        title.append(f"{game.mode.label.upper()} · {game.difficulty.label.upper()}", style=palette.muted)
        self.query_one("#game-title", Static).update(title)
        status = Text()
        status.append(f"ROUND {game.round_no}/{game.round_limit}  ", style=palette.muted)
        status.append(f"LIVES {lives}  ", style=palette.error if game.lives <= 1 else palette.success)
        status.append(f"SCORE {game.score}  ", style=palette.gold)
        status.append(f"STREAK {game.streak}", style=palette.accent2)
        self.query_one("#status-line", Static).update(status)
        kind = Text(game.puzzle.title.upper(), style=f"bold {palette.accent2}")
        self.query_one("#puzzle-kind", Static).update(kind)
        self.query_one("#puzzle-prompt", Static).update(
            Text(game.puzzle.prompt, style=f"bold {palette.text}")
        )
        answer = self.query_one("#answer", Input)
        answer.placeholder = PLACEHOLDERS.get(game.puzzle.kind, "answer")
        timer = self.query_one("#timer", ProgressBar)
        if game.mode.timed:
            timer.display = True
            timer.update(progress=int(game.time_ratio * 100))
            self.query_one("#timer", ProgressBar).styles.color = (
                palette.error if game.time_ratio < 0.25 else palette.accent
            )

    def _tick(self) -> None:
        if self._waiting:
            return
        outcome = self.game.tick(1)
        self._refresh_view()
        if outcome is not None:
            self._resolve(outcome)

    def on_input_submitted(self, event: Input.Submitted) -> None:
        if self._waiting:
            return
        if self.game.awaiting_next:
            self._advance()
            return
        answer = event.value.strip()
        if answer:
            self._resolve(self.game.submit(answer))

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "hint":
            self.action_hint()
        elif event.button.id == "skip":
            self.action_skip()
        elif event.button.id == "to-menu":
            self.action_menu()

    def action_hint(self) -> None:
        if self._waiting or self.game.awaiting_next:
            return
        hint = self.game.use_hint()
        if not hint:
            return
        palette = self.app.palette
        self.query_one("#feedback", Static).update(Text(f"Hint · {hint}", style=palette.gold))
        self.query_one("#hint", Button).disabled = True
        self._refresh_view()
        self.query_one("#answer", Input).focus()

    def action_skip(self) -> None:
        if self._waiting or self.game.awaiting_next:
            return
        outcome = self.game.submit("")
        self._resolve(outcome, skipped=True)

    def _resolve(self, outcome: Outcome, skipped: bool = False) -> None:
        self._waiting = True
        palette = self.app.palette
        answer = self.query_one("#answer", Input)
        answer.disabled = True
        for button_id in ("#hint", "#skip"):
            self.query_one(button_id, Button).disabled = True
        if outcome.correct:
            message = Text(f"{outcome.message}  Streak {outcome.streak}.", style=f"bold {palette.success}")
        else:
            prefix = "Skipped. " if skipped else ("Time. " if outcome.timed_out else "Not quite. ")
            message = Text(prefix + "Solution: " + outcome.solution, style=f"bold {palette.error}")
        self.query_one("#feedback", Static).update(message)
        self._refresh_view()
        if outcome.finished:
            new_best = self.app.store.record_run(self.game)
            self.set_timer(1.3, lambda: self.app.switch_screen(ResultsScreen(self.game, new_best)))
        else:
            self.set_timer(1.0, self._advance)

    def _advance(self) -> None:
        if not self.game.advance():
            return
        self._waiting = False
        answer = self.query_one("#answer", Input)
        answer.value = ""
        answer.disabled = False
        self.query_one("#hint", Button).disabled = False
        self.query_one("#skip", Button).disabled = False
        self.query_one("#feedback", Static).update("")
        self._refresh_view()
        answer.focus()

    def action_menu(self) -> None:
        self.app.switch_screen(MenuScreen())


class ResultsScreen(ThemedScreen):
    BINDINGS = [Binding("r", "replay", "Replay"), Binding("escape", "menu", "Menu")]

    def __init__(self, game: Game, new_best: bool) -> None:
        super().__init__()
        self.game = game
        self.new_best = new_best

    def compose(self) -> ComposeResult:
        palette = self.app.palette
        accuracy = self.game.accuracy
        grade = (
            "S" if accuracy >= 0.95 and self.game.solved >= 8 else
            "A" if accuracy >= 0.8 else
            "B" if accuracy >= 0.6 else
            "C"
        )
        achievements = achievements_for(self.app.store.profile, self.app.store.scores)[-3:]
        ach_text = " · ".join(f"{item.title}" for item in achievements) or "No badges yet"
        yield VerticalScroll(
            Vertical(
                Static(Text(f"{grade}  RUN COMPLETE", style=f"bold {palette.gold}"), id="result-grade"),
                Static(
                    Text(
                        f"Score {self.game.score}   ·   Solved {self.game.solved}/{self.game.attempts}   ·   "
                        f"Best streak {self.game.best_streak}",
                        style=palette.text,
                    ),
                    id="result-summary",
                ),
                Static(
                    Text(
                        ("NEW PERSONAL BEST  " if self.new_best else "")
                        + f"{self.game.mode.label} / {self.game.difficulty.label}",
                        style=palette.success if self.new_best else palette.muted,
                    ),
                    id="result-detail",
                ),
                Static(Text("BADGES · " + ach_text, style=palette.gold), id="achievements"),
                Horizontal(
                    Button("PLAY AGAIN [R]", id="replay"),
                    Button("STATS", id="stats"),
                    Button("MENU [ESC]", id="to-menu"),
                    id="result-buttons",
                ),
                id="result-card",
            ),
            classes="screen-scroll",
        )

    def on_mount(self) -> None:
        self.paint_palette()
        self.query_one("#replay", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "replay":
            self.action_replay()
        elif event.button.id == "stats":
            self.app.push_screen(StatsScreen())
        elif event.button.id == "to-menu":
            self.action_menu()

    def action_replay(self) -> None:
        self.app.start_game(self.game.mode.key)

    def action_menu(self) -> None:
        self.app.switch_screen(MenuScreen())


class StatsScreen(ThemedScreen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        palette = self.app.palette
        profile = self.app.store.profile
        scores = self.app.store.scores
        accuracy = accuracy_percent(profile)
        badges = achievements_for(profile, scores)
        modes = " · ".join(f"{mode} {count}" for mode, count in mode_counts(scores)) or "no runs yet"
        form = sparkline(recent_scores(scores)) or "no scores yet"
        yield VerticalScroll(
            Vertical(
                Static(Text("PLAYER RECORD", style=f"bold {palette.accent}"), id="result-grade"),
                Static(
                    Text(
                        f"Runs {profile.runs}   ·   Solved {profile.solved}   ·   "
                        f"Accuracy {accuracy:.1f}%   ·   Best streak {profile.best_streak}   ·   "
                        f"Best score {profile.best_score}",
                        style=palette.text,
                    ),
                    id="stats-summary",
                ),
                ProgressBar(total=100, show_eta=False, show_percentage=False, id="accuracy-bar"),
                Static(Text(f"ACCURACY {accuracy:.1f}%", style=palette.accent2), id="stats-label"),
                Static(Text(f"RECENT FORM  {form}", style=palette.gold), id="stats-form"),
                Static(Text(f"BY MODE  {modes}", style=palette.muted), id="stats-modes"),
                DataTable(id="stats-table"),
                Static(
                    Text(
                        "BADGES · " + (" · ".join(item.title for item in badges) or "none yet"),
                        style=palette.gold,
                    ),
                    id="achievements",
                ),
                Horizontal(Button("BACK [ESC]", id="back"), id="result-buttons"),
                id="stats-card",
            ),
            classes="screen-scroll",
        )

    def on_mount(self) -> None:
        self.paint_palette()
        profile = self.app.store.profile
        self.query_one("#accuracy-bar", ProgressBar).update(progress=round(accuracy_percent(profile)))
        table = self.query_one("#stats-table", DataTable)
        table.add_columns("SCORE", "MODE", "DIFFICULTY", "SOLVED", "STREAK", "DATE")
        for entry in self.app.store.scores[:10]:
            table.add_row(
                str(entry.score),
                entry.mode,
                entry.difficulty,
                f"{entry.solved}/{entry.attempts}",
                str(entry.best_streak),
                entry.date,
            )
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()


class HelpScreen(ThemedScreen):
    BINDINGS = [Binding("escape", "back", "Back")]

    def compose(self) -> ComposeResult:
        palette = self.app.palette
        body = Text()
        body.append("PUZZLE TYPES\n", style=f"bold {palette.accent}")
        body.append(
            "Equation · solve for x\n"
            "Missing number · find the hidden operand\n"
            "Operators · fill the gaps, evaluated left to right\n"
            "Sequence · continue the pattern\n"
            "True or false · type y or n\n"
            "Prime step · name the next prime\n"
            "Make 24 · use all four numbers exactly once\n\n",
            style=palette.text,
        )
        body.append("SCORING\n", style=f"bold {palette.accent}")
        body.append(
            "Answer quickly for a time bonus. Streaks multiply by up to 5×.\n"
            "A hint halves that puzzle's reward. A wrong answer or timeout costs one life.\n"
            "Zen has no timer and no death; Daily is seeded by today's date.\n\n",
            style=palette.muted,
        )
        body.append("CONTROLS\n", style=f"bold {palette.accent}")
        body.append(
            "ENTER submit · H hint · K skip · ESC menu · T theme · X difficulty",
            style=palette.text,
        )
        yield VerticalScroll(
            Vertical(
                Static(Text("HOW TO PLAY", style=f"bold {palette.accent}"), id="result-grade"),
                Static(body, id="help-body"),
                Horizontal(Button("BACK [ESC]", id="back"), id="result-buttons"),
                id="help-card",
            ),
            classes="screen-scroll",
        )

    def on_mount(self) -> None:
        self.paint_palette()
        self.query_one("#back", Button).focus()

    def on_button_pressed(self, event: Button.Pressed) -> None:
        if event.button.id == "back":
            self.action_back()

    def action_back(self) -> None:
        self.app.pop_screen()
