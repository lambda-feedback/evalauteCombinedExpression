# Combined response evaluation

Marks several related response areas together, so later answers can be checked against the student's own earlier answers.

Use a Table response area with one column and a row per answer. Name the rows (e.g. `$Re$`, `$L$`), and give the same names, in order, in the `labels` parameter: the row names aren't sent to the evaluation function. For the example below, set the parameters to `{"labels": ["Re", "L", "U", "nu", "Re"]}`.

What you write in each answer cell decides how that row is marked:

- **An expression**, e.g. `U*L/nu`: the student's expression must be equivalent (`L*U/nu` and `U/(nu/L)` are both accepted).
- **A range with units**, e.g. `0.001 m < L < 1 m`: the student must give a value with units (any equivalent units, e.g. `50 cm`) between the bounds. Use `<=` to include a bound.
- **A calculation**, e.g. `Re = U*L/nu`: the student's value must match the formula evaluated with *their own* values from the range rows, within 1% (change with the `rtol` parameter). A student who chose an out-of-range length is marked wrong once, on that row, not again here.

Example (Reynolds number):

| Label | Answer |
|---|---|
| Re | `U*L/nu` |
| L | `0.001 m < L < 1 m` |
| U | `0.001 m/s < U < 1 m/s` |
| nu | `1e-7 m^2/s < nu < 1e-4 m^2/s` |
| Re | `Re = U*L/nu` |
