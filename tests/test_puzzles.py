from __future__ import annotations

import random

import pytest

from solvamath.game import Game
from solvamath.models import DIFFICULTY_ORDER
from solvamath.puzzles import check_answer, daily_seed, make_puzzle, safe_eval_expression


def test_every_puzzle_kind_accepts_its_answer() -> None:
    seen = set()
    for difficulty in DIFFICULTY_ORDER:
        rng = random.Random(20261118)
        for _ in range(80):
            puzzle = make_puzzle(rng, difficulty)
            seen.add(puzzle.kind)
            candidate = (
                puzzle.solution.split("=")[0].strip()
                if puzzle.kind == "target"
                else puzzle.answer
            )
            assert check_answer(puzzle, candidate), puzzle
            assert not check_answer(puzzle, "definitely wrong"), puzzle
    assert {"equation", "missing_number", "sequence", "true_false", "operators", "prime"} <= seen


def test_target_requires_all_numbers_once() -> None:
    rng = random.Random(4)
    puzzle = make_puzzle(rng, "expert")
    while puzzle.kind != "target":
        puzzle = make_puzzle(rng, "expert")
    assert check_answer(puzzle, puzzle.solution.split("=")[0].strip())
    assert not check_answer(puzzle, "24")
    assert not check_answer(puzzle, "1 + 2 + 3 + 4")
    assert not check_answer(puzzle, "6 * 6")


def test_safe_evaluator_rejects_code_and_unknown_names() -> None:
    assert safe_eval_expression("(6 + 6) * 2") == 24
    for bad in ("__import__('os')", "x + 1", "2 ** 100000000", "1 / 0", "1;2"):
        with pytest.raises(ValueError):
            safe_eval_expression(bad)


def test_daily_seed_and_generation_are_deterministic() -> None:
    first = [make_puzzle(random.Random(1234), "normal") for _ in range(8)]
    second = [make_puzzle(random.Random(1234), "normal") for _ in range(8)]
    assert first == second
    assert daily_seed() > 20000000


def test_game_scores_correct_answers_and_advances() -> None:
    game = Game("campaign", "easy", seed=7)
    result = game.submit(game.puzzle.answer)
    assert result.correct
    assert result.points > 0
    assert game.streak == 1
    assert game.attempts == 1
    assert game.advance()
    assert game.round_no == 2


def test_game_loses_life_on_wrong_answer_and_timeout() -> None:
    game = Game("campaign", "easy", seed=9)
    result = game.submit("wrong")
    assert not result.correct
    assert game.lives == 2
    game.advance()
    game.time_left = 1
    result = game.tick(1)
    assert result is not None
    assert result.timed_out
    assert game.lives == 1


def test_hint_costs_score_and_is_returned() -> None:
    game = Game("campaign", "easy", seed=11)
    hint = game.use_hint()
    assert hint == game.puzzle.hint
    assert game.hint_used
    assert game.score == 0


def test_zen_has_no_timer_or_death() -> None:
    game = Game("zen", "normal", seed=21)
    assert not game.mode.timed
    assert game.lives == 999
    assert game.tick(9) is None


def test_run_finishes_after_round_limit() -> None:
    game = Game("campaign", "easy", seed=31)
    for _ in range(game.round_limit):
        result = game.submit(game.puzzle.answer)
        if not result.finished:
            game.advance()
    assert game.finished
