# Combined response evaluation

Marks several related response areas together, so later answers can be checked against the student's own earlier answers.

Set the answer as a list of `[label, answer]` rows, one per response area, in order:

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
