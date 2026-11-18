"""CLI entry point for Solvamath."""

from __future__ import annotations

import argparse
from collections.abc import Sequence

from . import __version__
from .models import DIFFICULTY_ORDER
from .storage import Store
from .theme import THEME_ORDER


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="solvamath",
        description="A full-featured terminal math puzzle game.",
    )
    parser.add_argument("--version", action="version", version=f"solvamath {__version__}")
    parser.add_argument("--daily", action="store_true", help="start today's shared daily run")
    parser.add_argument("--difficulty", choices=DIFFICULTY_ORDER, help="set difficulty for this launch")
    parser.add_argument("--theme", choices=THEME_ORDER, help="set the color theme")
    parser.add_argument("--stats", action="store_true", help="print persistent stats and exit")
    parser.add_argument("--seed", type=int, help="use a fixed puzzle seed (testing/replays)")
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


def main(argv: Sequence[str] | None = None) -> int:
    args = build_parser().parse_args(argv)
    store = Store()
    if args.difficulty:
        store.update_settings(difficulty=args.difficulty)
    if args.theme:
        store.update_settings(theme=args.theme)
    if args.stats:
        print_stats(store)
        return 0
    from .app import SolvamathApp

    start_mode = "daily" if args.daily else (
        "campaign" if args.seed is not None else None
    )
    app = SolvamathApp(store=store, start_mode=start_mode, seed=args.seed)
    app.run()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
