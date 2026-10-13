# Combined response evaluation
Evaluates several related response areas together. Each answer row decides how its response is checked: a symbolic expression, a quantity with units within a range, or a value computed from the student's own quantities in other rows (error carried forward).

Parsing and units come from the `lambdafeedback-expression-parsing` and `lambdafeedback-units` packages (extracted from compareExpressions), installed as git dependencies. They are only used through `evaluation_function/backend.py`.

## Inputs
`response` and `answer` are 2D lists of `[label, value]` rows, matched by position. The labels must match.

The answer row's value decides the row type:

| Answer value | Row type | Response is correct when |
|---|---|---|
| `<lower> < LABEL < <upper>` (`<` or `<=`) | range | it is a quantity within the bounds. If the bounds have units, the response must have the same units (any convertible unit is accepted, e.g. `cm` for `m`). Bare-number bounds are compared in SI units with no unit check. |
| `LABEL = <expression>` | computed | it equals the expression evaluated with the student's quantities from the range rows (same SI units, within `rtol`). |
| anything else | expression | it is symbolically equivalent to the answer. Every row label is treated as a single symbol, so `nu` is not read as `n*u`. |

Values in computed rows use the student's own range-row quantities even if those are out of range, so a student is only marked down once for a wrong value.

### Params
- `rtol` (default `0.01`): relative tolerance for computed rows.
- Other keys (e.g. `units_string`, `strictness`, `symbols`) are passed through to the parsing packages.

## Outputs
`is_correct` is true only if every row is correct. `feedback` has one line per incorrect row, prefixed with its label. Each row's feedback has the tag `row_<n>`.

A malformed `answer` raises `ValueError`. A malformed `response` is marked incorrect with feedback.

## Examples

### Reynolds number

```python
answer = [
    ["Re", "U*L/nu"],
    ["L", "0.001 m < L < 1 m"],
    ["U", "0.001 m/s < U < 1 m/s"],
    ["nu", "1e-7 m^2/s < nu < 1e-4 m^2/s"],
    ["Re", "Re = U*L/nu"],
]
response = [["Re", "U/(nu/L)"], ["L", "50 cm"], ["U", "0.72 km/h"], ["nu", "0.01 cm^2/s"], ["Re", "1e5"]]
```

```python
{"is_correct": True, "feedback": ""}
```

With `["nu", "0.2 m"]` and `["Re", "1.2e5"]` instead:

```python
{"is_correct": False, "feedback": "nu: the units are not correct.<br>Re: the units are not consistent with your other answers."}
```

## Development

```bash
poetry install
poetry run pytest
poetry run evaluation_function_dev '<response json>' '<answer json>' ['<params json>']
```

Python 3.11–3.12 only: latex2sympy2 pins antlr4 4.7.2, which doesn't import on 3.13.
