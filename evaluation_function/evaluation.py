from typing import Any, Optional

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


def _labels(params: dict) -> Optional[list[str]]:
    """The ``labels`` param: one label per row, for single-column tables."""
    labels = params.get("labels")
    if labels is None:
        return None
    if not isinstance(labels, list) or not all(isinstance(label, str) for label in labels):
        raise ValueError("The labels parameter must be a list of strings.")
    return labels


def _rows(value: Any, name: str, labels: Optional[list[str]] = None) -> list[tuple[str, str]]:
    """Validate a 2D list of ``[label, value]`` rows.

    With ``labels``, rows may instead be single ``[value]`` cells (a one-column
    Table response area, which doesn't send its row names), and are paired
    with the labels by position.

    Labels may be written as LaTeX (``$nu$``); the ``$`` are stripped so the
    label matches the plain name used in the answers.
    """
    if not isinstance(value, list) or not all(isinstance(row, list) for row in value):
        raise ValueError(f"The {name} must be a list of rows.")
    if labels is not None and all(len(row) == 1 for row in value):
        if len(value) != len(labels):
            raise ValueError(f"The {name} has {len(value)} rows, but {len(labels)} labels were given.")
        value = [[label, row[0]] for label, row in zip(labels, value)]
    elif not all(len(row) == 2 for row in value):
        raise ValueError(
            f"The {name} must be a list of [label, value] rows, or of [value] rows with the labels parameter."
        )
    return [(str(label).strip().strip("$").strip(), str(text).strip()) for label, text in value]


def evaluation_function(
    response: Any,
    answer: Any,
    params: Params,
) -> Result:
    """
    Evaluate several related response areas together.

    `response` and `answer` are 2D lists of `[label, value]` rows, matched by
    position, or of `[value]` rows when the `labels` param is given. Each
    answer row's text decides how its response is checked (see `rows.py`): a
    symbolic expression, a quantity within a range, or a value computed from
    the student's own quantities in other rows.

    Params:
    - `rtol`: relative tolerance for computed rows (default 0.01).
    - `labels`: one label per row, for single-column rows.
    """
    params = dict(params or {})
    labels = _labels(params)
    answer_rows = _rows(answer, "answer", labels)
    try:
        response_rows = _rows(response, "response", labels)
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
