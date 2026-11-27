"""CLI entry point for Solvamath."""

from __future__ import annotations

import argparse
import random
from collections.abc import Sequence

from . import __version__
from .models import DIFFICULTIES, DIFFICULTY_ORDER
from .puzzles import check_answer, make_puzzle
from .storage import Store
from .theme import THEME_ORDER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solvamath",
        description="A full-featured terminal math puzzle game.",
    )
    parser.add_argument("--version", "-v", action="version", version=f"solvamath {__version__}")
    parser.add_argument("--daily", action="store_true", help="start today's shared daily run")
    parser.add_argument("--difficulty", choices=DIFFICULTY_ORDER, help="set difficulty for this launch")
    parser.add_argument("--theme", choices=THEME_ORDER, help="set the color theme")
    parser.add_argument("--stats", action="store_true", help="print persistent stats and exit")
    parser.add_argument("--repl", action="store_true", help="practice puzzles in a REPL")
    parser.add_argument("--seed", type=int, help="use a fixed puzzle seed (testing/replays)")
    parser.add_argument("--list-themes", action="store_true", help="print available themes and exit")
    return parser


def print_stats(store: Store) -> None:
    profile = store.profile
    accuracy = profile.solved / profile.attempts * 100 if profile.attempts else 0.0
    print("Solvamath record")
    print(f"  runs        {profile.runs}")
    print(f"  solved      {profile.solved}/{profile.attempts}  ({accuracy:.1f}%)")
    print(f"  best streak {profile.best_streak}")
    print(f"  best score  {profile.best_score}")
    if store.scores:
        print("\nTop scores")
        for entry in store.scores[:5]:
            print(
                f"  {entry.score:>6}  {entry.mode[:8]:<8} {entry.difficulty:<7} "
                f"{entry.solved}/{entry.attempts}  {entry.date}"
            )


def _show_puzzle(puzzle, difficulty: str) -> None:
    print(f"\n{puzzle.title.upper()}  ·  {DIFFICULTIES[difficulty].label}")
    print(puzzle.prompt)


def run_repl(store: Store) -> int:
    """Practice puzzles with a persistent score record and simple commands."""
    rng = random.Random()
    difficulty = store.settings.difficulty
    puzzle = make_puzzle(rng, difficulty)
    solved = tried = 0
    print("Solvamath REPL — solve puzzles here; type help for commands.")
    _show_puzzle(puzzle, difficulty)
    while True:
        try:
            line = input("solvamath> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            line = "quit"
        command, _, rest = line.partition(" ")
        command = command.lower()
        if command in {"quit", "exit"}:
            if solved or tried:
                print(f"session: {solved} solved / {tried} attempts")
            return 0
        if not line:
            continue
        if command == "help":
            print("  <answer>        answer the current puzzle")
            print("  hint            show a hint")
            print("  skip            reveal the answer and move on")
            print("  difficulty [x]  show or set Easy/Normal/Hard/Expert")
            print("  stats           show your persistent record")
            print("  theme [name]    show or set the TUI theme")
            print("  quit / exit     leave the REPL")
            continue
        if command == "hint":
            print(f"hint: {puzzle.hint}")
            continue
        if command == "skip":
            print(f"answer: {puzzle.answer}")
            puzzle = make_puzzle(rng, difficulty)
            _show_puzzle(puzzle, difficulty)
            continue
        if command == "stats":
            print(f"session: {solved} solved / {tried} attempts")
            print_stats(store)
            continue
        if command == "difficulty":
            name = rest.strip().lower()
            if not name:
                print(f"difficulty: {difficulty}")
            elif name not in DIFFICULTY_ORDER:
                print(f"unknown difficulty: {name} (try {', '.join(DIFFICULTY_ORDER)})")
            else:
                difficulty = name
                store.update_settings(difficulty=name)
                puzzle = make_puzzle(rng, difficulty)
                print(f"difficulty: {name}")
                _show_puzzle(puzzle, difficulty)
            continue
        if command == "theme":
            name = rest.strip().lower()
            if not name:
                print(f"theme: {store.settings.theme}")
            elif name not in THEME_ORDER:
                print(f"unknown theme: {name} (try {', '.join(THEME_ORDER)})")
            else:
                store.update_settings(theme=name)
                print(f"theme: {name}")
            continue

        tried += 1
        if check_answer(puzzle, line):
            solved += 1
            print("correct — next puzzle")
            puzzle = make_puzzle(rng, difficulty)
            _show_puzzle(puzzle, difficulty)
        else:
            print("not quite — try again, or type hint / skip")


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store()
    if args.list_themes:
        print("available themes: " + ", ".join(THEME_ORDER))
        return 0
    if args.difficulty:
        store.update_settings(difficulty=args.difficulty)
    if args.theme:
        store.update_settings(theme=args.theme)
    if args.stats:
        print_stats(store)
        return 0
    if args.repl:
        return run_repl(store)
    from .app import SolvamathApp

    start_mode = "daily" if args.daily else (
        "campaign" if args.seed is not None else None
    )
    app = SolvamathApp(store=store, start_mode=start_mode, seed=args.seed)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
