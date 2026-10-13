"""Answer-row types and the checks for each.

The type of an answer row is inferred from its text:

- ``"<lower> < L < <upper>"`` (``<`` or ``<=``) is a :class:`RangeSpec`:
  the response must be a quantity within the bounds, with the bounds' units.
- ``"Re = U*L/nu"`` (the row's own label, then ``=``) is a
  :class:`ComputedSpec`: the response must equal the expression evaluated with
  the student's own values from the range rows.
- Anything else is an :class:`ExpressionSpec`: the response must be
  symbolically equivalent to the answer.
"""

import re
from dataclasses import dataclass
from typing import Any, Mapping, Optional, Union

import sympy

from .backend import (
    BackendError,
    Quantity,
    evaluate_with_quantities,
    expressions_equivalent,
    parse_quantity,
    parse_symbolic,
    units_compatible,
)


@dataclass(frozen=True)
class ExpressionSpec:
    expression: str


@dataclass(frozen=True)
class RangeSpec:
    lower: Quantity
    lower_inclusive: bool
    upper: Quantity
    upper_inclusive: bool


@dataclass(frozen=True)
class ComputedSpec:
    expression: str


Spec = Union[ExpressionSpec, RangeSpec, ComputedSpec]


@dataclass(frozen=True)
class RowResult:
    correct: bool
    feedback: str = ""
    quantity: Optional[Quantity] = None


def parse_spec(label: str, text: str, params: Mapping[str, Any]) -> Spec:
    """Work out the row type from the answer text (see the module docstring)."""
    name = re.escape(label)
    range_match = re.fullmatch(rf"\s*(.+?)\s*(<=|<)\s*{name}\s*(<=|<)\s*(.+?)\s*", text)
    if range_match:
        lower, lower_op, upper_op, upper = range_match.groups()
        return RangeSpec(
            parse_quantity(lower, params), lower_op == "<=", parse_quantity(upper, params), upper_op == "<="
        )
    computed_match = re.fullmatch(rf"\s*{name}\s*=\s*(.+?)\s*", text)
    if computed_match:
        return ComputedSpec(computed_match.group(1))
    return ExpressionSpec(text)


def check_expression(
    label: str, response: str, spec: ExpressionSpec, symbols: list[str], params: Mapping[str, Any]
) -> RowResult:
    try:
        correct = expressions_equivalent(response, spec.expression, symbols, params)
    except BackendError as e:
        return RowResult(False, f"{label}: {e}")
    return RowResult(correct, "" if correct else f"{label}: the expression is not correct.")


def check_range(label: str, response: str, spec: RangeSpec, params: Mapping[str, Any]) -> RowResult:
    try:
        quantity = parse_quantity(response, params)
    except BackendError as e:
        return RowResult(False, f"{label}: {e}")

    bounds_have_units = spec.lower.has_unit or spec.upper.has_unit
    if bounds_have_units and not units_compatible(quantity, spec.lower):
        message = "the units are missing." if not quantity.has_unit else "the units are not correct."
        return RowResult(False, f"{label}: {message}", quantity)

    value = quantity.value
    above = value >= spec.lower.value if spec.lower_inclusive else value > spec.lower.value
    below = value <= spec.upper.value if spec.upper_inclusive else value < spec.upper.value
    if not (above and below):
        return RowResult(
            False, f"{label}: the value should be between {spec.lower.text} and {spec.upper.text}.", quantity
        )
    return RowResult(True, "", quantity)


def check_computed(
    label: str,
    response: str,
    spec: ComputedSpec,
    quantities: Mapping[str, Quantity],
    symbols: list[str],
    params: Mapping[str, Any],
) -> RowResult:
    try:
        needed = sorted(str(s) for s in parse_symbolic(spec.expression, symbols, params).free_symbols)
    except BackendError as e:
        raise ValueError(f"Answer for {label}: {e}") from e
    missing = [name for name in needed if name not in quantities]
    if missing:
        return RowResult(False, f"{label}: can't be checked until {', '.join(missing)} can be read.")

    try:
        quantity = parse_quantity(response, params)
    except BackendError as e:
        return RowResult(False, f"{label}: {e}")

    expected = evaluate_with_quantities(spec.expression, {name: quantities[name] for name in needed}, params)
    ratio = sympy.simplify(quantity.si / expected) if expected != 0 else None
    if ratio is None or ratio.free_symbols:
        return RowResult(False, f"{label}: the units are not consistent with your other answers.", quantity)

    rtol = float(params.get("rtol", 0.01))
    if abs(float(ratio) - 1) > rtol:
        return RowResult(False, f"{label}: the value does not follow from your other answers.", quantity)
    return RowResult(True, "", quantity)
