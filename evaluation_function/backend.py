"""Thin adapter over the lambdafeedback parsing and units packages.

The rest of the evaluation function only uses the functions defined here, so
the packages can change underneath without touching the row logic.
"""

from dataclasses import dataclass
from typing import Any, Iterable, Mapping

import sympy
from lambdafeedback.expression_parsing import (
    ExpressionParams,
    ExpressionParsingError,
    SympyParsingConfig,
    parse_expression,
    preprocess_expression,
)
from lambdafeedback.units import QuantityError, QuantityParams, parse_quantity as _parse_quantity


class BackendError(ValueError):
    """An input could not be read."""


@dataclass(frozen=True)
class Quantity:
    """A number with an optional unit, converted to SI base units.

    ``unit`` is a SymPy expression in base-unit symbols (``metre``,
    ``second``, ...), or ``1`` when no unit was given.
    """

    text: str
    value: sympy.Expr
    unit: sympy.Expr
    has_unit: bool

    @property
    def si(self) -> sympy.Expr:
        return self.value * self.unit


def parse_quantity(text: str, params: Mapping[str, Any]) -> Quantity:
    """Read ``text`` (e.g. ``"50 cm"``) as a numeric quantity in SI units."""
    try:
        q = _parse_quantity(text, QuantityParams.from_dict(params))
    except (QuantityError, ExpressionParsingError) as e:
        raise BackendError(f"Could not read '{text}' as a quantity.") from e
    if q.value is None or not q.standard_values:
        raise BackendError(f"'{text}' has no numerical value.")
    if len(q.standard_values) > 1:
        raise BackendError(f"Expected a single value, got '{text}'.")
    (value,) = q.standard_values
    if value.free_symbols:
        raise BackendError(f"Could not read the value in '{text}' as a number.")
    has_unit = q.unit is not None
    unit = q.standard_unit if has_unit else sympy.Integer(1)
    return Quantity(text, sympy.nsimplify(value), unit, has_unit)


def units_compatible(a: Quantity, b: Quantity) -> bool:
    """True if the two quantities have the same SI units (i.e. the same dimension)."""
    return not sympy.simplify(a.unit / b.unit).free_symbols


def parse_symbolic(text: str, symbols: Iterable[str], params: Mapping[str, Any]) -> sympy.Expr:
    """Parse an expression, treating every name in ``symbols`` as a single symbol."""
    symbols = tuple(symbols)
    try:
        expression_params = ExpressionParams.from_dict(params)
        config = SympyParsingConfig.from_params(expression_params, unsplittable_symbols=symbols)
        expr = parse_expression(preprocess_expression(text, expression_params, name="response"), config)
    except ExpressionParsingError as e:
        raise BackendError(f"Could not parse the expression '{text}'.") from e
    if isinstance(expr, sympy.Equality):
        return expr.lhs - expr.rhs
    return expr


def expressions_equivalent(response: str, answer: str, symbols: Iterable[str], params: Mapping[str, Any]) -> bool:
    """True if the two expressions are symbolically equal."""
    symbols = tuple(symbols)
    difference = parse_symbolic(response, symbols, params) - parse_symbolic(answer, symbols, params)
    return sympy.simplify(difference) == 0


def evaluate_with_quantities(
    expr: str, quantities: Mapping[str, Quantity], params: Mapping[str, Any]
) -> sympy.Expr:
    """Substitute each quantity (value times SI unit) into ``expr`` and simplify."""
    parsed = parse_symbolic(expr, quantities.keys(), params)
    substitutions = {sympy.Symbol(name): q.si for name, q in quantities.items()}
    return sympy.simplify(parsed.subs(substitutions))
