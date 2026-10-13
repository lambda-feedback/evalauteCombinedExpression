from typing import Any

from lf_toolkit.evaluation import Result, Params

from .backend import BackendError
from .rows import (
    ComputedSpec,
    ExpressionSpec,
    RangeSpec,
    check_computed,
    check_expression,
    check_range,
    parse_spec,
)


def _rows(value: Any, name: str) -> list[tuple[str, str]]:
    """Validate a 2D list of ``[label, value]`` rows."""
    if not isinstance(value, list) or not all(isinstance(row, list) and len(row) == 2 for row in value):
        raise ValueError(f"The {name} must be a list of [label, value] rows.")
    return [(str(label).strip(), str(text).strip()) for label, text in value]


def evaluation_function(
    response: Any,
    answer: Any,
    params: Params,
) -> Result:
    """
    Evaluate several related response areas together.

    `response` and `answer` are 2D lists of `[label, value]` rows, matched by
    position. Each answer row's text decides how its response is checked (see
    `rows.py`): a symbolic expression, a quantity within a range, or a value
    computed from the student's own quantities in other rows.

    Params:
    - `rtol`: relative tolerance for computed rows (default 0.01).
    """
    answer_rows = _rows(answer, "answer")
    try:
        response_rows = _rows(response, "response")
    except ValueError as e:
        return Result(is_correct=False, feedback_items=[("format", str(e))])

    if len(response_rows) != len(answer_rows):
        return Result(
            is_correct=False,
            feedback_items=[("format", f"Expected {len(answer_rows)} answers, got {len(response_rows)}.")],
        )
    for i, ((label, _), (expected, _)) in enumerate(zip(response_rows, answer_rows), start=1):
        if label != expected:
            return Result(
                is_correct=False,
                feedback_items=[("format", f"Row {i} should be '{expected}', got '{label}'.")],
            )

    params = dict(params or {})
    symbols = sorted({label for label, _ in answer_rows})
    try:
        specs = [parse_spec(label, text, params) for label, text in answer_rows]
    except BackendError as e:
        raise ValueError(f"Could not read the answer: {e}") from e

    results = [None] * len(specs)
    quantities = {}
    for i, ((label, text), spec) in enumerate(zip(response_rows, specs)):
        if not text:
            continue
        if isinstance(spec, ExpressionSpec):
            results[i] = check_expression(label, text, spec, symbols, params)
        elif isinstance(spec, RangeSpec):
            results[i] = check_range(label, text, spec, params)
            if results[i].quantity is not None:
                quantities[label] = results[i].quantity

    for i, ((label, text), spec) in enumerate(zip(response_rows, specs)):
        if text and isinstance(spec, ComputedSpec):
            results[i] = check_computed(label, text, spec, quantities, symbols, params)

    result = Result(is_correct=True)
    for i, ((label, _), row) in enumerate(zip(response_rows, results), start=1):
        if row is None:
            result.is_correct = False
            result.add_feedback(f"row_{i}", f"{label}: no answer given.")
        elif not row.correct:
            result.is_correct = False
            result.add_feedback(f"row_{i}", row.feedback)
    return result
