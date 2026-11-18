"""Puzzle generation and answer checking. No Textual imports."""

from __future__ import annotations

import ast
import math
import random
import re
from datetime import date

from .models import DIFFICULTIES, Puzzle

TARGET_SETS = (
    ((1, 2, 3, 4), "1 * 2 * 3 * 4"),
    ((4, 6, 6, 8), "6 * 6 - 8 - 4"),
    ((1, 3, 4, 6), "6 / (1 - 3 / 4)"),
    ((2, 3, 4, 6), "6 * 4 * (3 - 2)"),
    ((2, 3, 4, 5), "(5 - 2 + 3) * 4"),
    ((3, 3, 8, 8), "8 / (3 - 8 / 3)"),
    ((4, 4, 10, 10), "(10 * 10 - 4) / 4"),
    ((5, 5, 5, 1), "5 * (5 - 1 / 5)"),
)
PRIMES = (2, 3, 5, 7, 11, 13, 17, 19, 23, 29, 31, 37, 41, 43, 47, 53, 59, 61, 67, 71, 73, 79, 83, 89, 97)


def daily_seed(day: date | None = None) -> int:
    return int((day or date.today()).strftime("%Y%m%d"))


def _is_prime(n: int) -> bool:
    if n < 2:
        return False
    if n % 2 == 0:
        return n == 2
    d = 3
    while d <= n // d:
        if n % d == 0:
            return False
        d += 2
    return True


def _next_prime(n: int) -> int:
    value = max(2, n + 1)
    while not _is_prime(value):
        value += 1
    return value


def safe_eval_expression(text: str) -> float:
    """Evaluate a tiny arithmetic language without eval()."""
    if not text or len(text) > 80:
        raise ValueError("expression is empty or too long")
    if any(ch not in "0123456789+-*/(). " for ch in text):
        raise ValueError("only numbers and + - * / ( ) are allowed")
    try:
        tree = ast.parse(text, mode="eval")
    except SyntaxError as exc:
        raise ValueError("invalid expression") from exc
    nodes = 0

    def walk(node: ast.AST) -> float:
        nonlocal nodes
        nodes += 1
        if nodes > 80:
            raise ValueError("expression is too complex")
        if isinstance(node, ast.Expression):
            return walk(node.body)
        if isinstance(node, ast.Constant) and isinstance(node.value, int | float):
            value = float(node.value)
        elif isinstance(node, ast.UnaryOp) and isinstance(node.op, ast.USub | ast.UAdd):
            value = walk(node.operand)
            value = -value if isinstance(node.op, ast.USub) else value
        elif isinstance(node, ast.BinOp) and isinstance(node.op, ast.Add | ast.Sub | ast.Mult | ast.Div):
            left = walk(node.left)
            right = walk(node.right)
            if isinstance(node.op, ast.Add):
                value = left + right
            elif isinstance(node.op, ast.Sub):
                value = left - right
            elif isinstance(node.op, ast.Mult):
                value = left * right
            else:
                if right == 0:
                    raise ValueError("division by zero")
                value = left / right
        else:
            raise ValueError("unsupported expression")
        if not math.isfinite(value) or abs(value) > 1e12:
            raise ValueError("result out of range")
        return value

    return walk(tree)


def _numeric_answer(value: int | float) -> str:
    return str(int(value)) if float(value).is_integer() else str(round(value, 6))


def _signed(value: int) -> str:
    return f"+ {value}" if value >= 0 else f"- {abs(value)}"


def _equation(rng: random.Random) -> Puzzle:
    a = rng.randint(2, 9)
    x = rng.randint(1, 12)
    b = rng.randint(-12, 15)
    c = a * x + b
    return Puzzle(
        "equation",
        "Solve for x",
        f"{a}x {_signed(b)} = {c}",
        str(x),
        "Move the constant first, then divide by the multiplier.",
        f"x = {x}",
    )


def _missing_number(rng: random.Random) -> Puzzle:
    op = rng.choice("+-*")
    a = rng.randint(2, 12)
    b = rng.randint(1, 12)
    if op == "+":
        result = a + b
        prompt = f"{a} + ? = {result}"
        why = f"Subtract {a} from {result}."
    elif op == "-":
        result = a - b
        prompt = f"{a} - ? = {result}"
        why = f"Subtract {result} from {a}."
    else:
        result = a * b
        prompt = f"{a} × ? = {result}"
        why = f"Divide {result} by {a}."
    return Puzzle("missing_number", "Find the missing number", prompt, str(b), why, f"answer = {b}")


def _operators(rng: random.Random) -> Puzzle:
    for _ in range(50):
        count = rng.choice((2, 3))
        numbers = [rng.randint(1, 9) for _ in range(count + 1)]
        operators = [rng.choice("+-*/") for _ in range(count)]
        value = float(numbers[0])
        ok = True
        for op, number in zip(operators, numbers[1:], strict=False):
            if op == "+":
                value += number
            elif op == "-":
                value -= number
            elif op == "*":
                value *= number
            else:
                if number == 0:
                    ok = False
                    break
                value /= number
        if ok and value.is_integer() and 0 <= value <= 100:
            expression = " ".join(
                [str(numbers[0])] + [f"{op} {number}" for op, number in zip(operators, numbers[1:], strict=False)]
            )
            return Puzzle(
                "operators",
                "Fill the operators",
                " ? ".join(map(str, numbers)) + f" = {int(value)}  ·  left to right",
                "".join(operators),
                f"Start with {operators[0]}; use only + - * / once per gap.",
                expression + f" = {int(value)}",
            )
    return _missing_number(rng)


def _sequence(rng: random.Random) -> Puzzle:
    style = rng.choice(("arithmetic", "geometric", "squares"))
    if style == "arithmetic":
        start, step = rng.randint(1, 9), rng.randint(2, 9)
        values = [start + index * step for index in range(5)]
        why = f"Each value grows by {step}."
        solution = f"next = {values[-1]}"
    elif style == "geometric":
        start, ratio = rng.randint(1, 5), rng.choice((2, 3))
        values = [start * (ratio ** index) for index in range(5)]
        why = f"Each value is multiplied by {ratio}."
        solution = f"next = {values[-1]}"
    else:
        start = rng.randint(2, 6)
        values = [(start + index) ** 2 for index in range(5)]
        why = "The sequence follows consecutive squares."
        solution = f"next = {values[-1]}"
    return Puzzle(
        "sequence",
        "Continue the sequence",
        "  ".join(f"{value:,}" for value in values[:4]) + "  ?",
        str(values[4]),
        why,
        solution,
    )


def _true_false(rng: random.Random) -> Puzzle:
    a, b = rng.randint(2, 12), rng.randint(2, 12)
    op = rng.choice("+-*")
    actual = {"+": a + b, "-": a - b, "*": a * b}[op]
    truthful = rng.random() < 0.5
    shown = actual if truthful else actual + rng.choice((-2, -1, 1, 2))
    symbol = {"+": "+", "-": "−", "*": "×"}[op]
    return Puzzle(
        "true_false",
        "True or false?",
        f"{a} {symbol} {b} = {shown}",
        "yes" if truthful else "no",
        "Work out the left side first. Type y or n.",
        f"{a} {symbol} {b} = {actual}, so the statement is {'true' if truthful else 'false'}.",
    )


def _prime(rng: random.Random) -> Puzzle:
    base = rng.choice(PRIMES)
    answer = _next_prime(base)
    return Puzzle(
        "prime",
        "Prime step",
        f"What is the next prime after {base}?",
        str(answer),
        "Try the next odd numbers and test divisibility.",
        f"{answer} is the first prime after {base}.",
    )


def _target(rng: random.Random) -> Puzzle:
    numbers, solution = rng.choice(TARGET_SETS)
    return Puzzle(
        "target",
        "Make 24",
        "Use " + ", ".join(map(str, numbers)) + " exactly once to make 24",
        "",
        "Combine two values first; division can create a useful fraction.",
        solution + " = 24",
        tuple(numbers),
        24,
    )


GENERATORS = {
    "equation": _equation,
    "missing_number": _missing_number,
    "operators": _operators,
    "sequence": _sequence,
    "true_false": _true_false,
    "prime": _prime,
    "target": _target,
}


def make_puzzle(rng: random.Random, difficulty_key: str = "normal") -> Puzzle:
    difficulty = DIFFICULTIES.get(difficulty_key, DIFFICULTIES["normal"])
    return GENERATORS[rng.choice(difficulty.kinds)](rng)


def check_answer(puzzle: Puzzle, raw: str) -> bool:
    answer = str(raw or "").strip().lower()
    if puzzle.kind == "target":
        try:
            numbers = tuple(sorted(int(value) for value in re.findall(r"\d+", answer)))
        except ValueError:
            return False
        if numbers != tuple(sorted(puzzle.numbers)):
            return False
        try:
            return abs(safe_eval_expression(answer) - 24) < 1e-9
        except ValueError:
            return False
    if puzzle.kind == "operators":
        return answer.replace(" ", "").replace("×", "*").replace("÷", "/") == puzzle.answer
    if puzzle.kind == "true_false":
        return (answer in {"y", "yes", "true", "1"}) if puzzle.answer == "yes" else (
            answer in {"n", "no", "false", "0"}
        )
    try:
        return float(answer) == float(puzzle.answer)
    except ValueError:
        return False
