import unittest

import sympy

from .backend import (
    BackendError,
    evaluate_with_quantities,
    expressions_equivalent,
    parse_quantity,
    units_compatible,
)


class TestBackend(unittest.TestCase):
    def test_parse_quantity_converts_to_si(self):
        q = parse_quantity("20 cm", {})
        self.assertEqual(q.value, sympy.Rational(1, 5))
        self.assertTrue(q.has_unit)
        self.assertTrue(units_compatible(q, parse_quantity("1 m", {})))

    def test_parse_quantity_km_per_hour(self):
        q = parse_quantity("2 km/h", {})
        self.assertEqual(q.value, sympy.Rational(5, 9))
        self.assertTrue(units_compatible(q, parse_quantity("1 m/s", {})))
        self.assertFalse(units_compatible(q, parse_quantity("1 m", {})))

    def test_parse_quantity_without_unit(self):
        q = parse_quantity("1e5", {})
        self.assertEqual(q.value, 100000)
        self.assertFalse(q.has_unit)

    def test_parse_quantity_rejects_non_numbers(self):
        with self.assertRaises(BackendError):
            parse_quantity("abc", {})

    def test_expressions_equivalent(self):
        symbols = ["U", "L", "nu"]
        self.assertTrue(expressions_equivalent("U/(nu/L)", "U*L/nu", symbols, {}))
        self.assertFalse(expressions_equivalent("U*nu/L", "U*L/nu", symbols, {}))

    def test_evaluate_with_quantities_is_dimensionless(self):
        quantities = {
            "L": parse_quantity("50 cm", {}),
            "U": parse_quantity("0.2 m/s", {}),
            "nu": parse_quantity("1e-6 m^2/s", {}),
        }
        result = evaluate_with_quantities("U*L/nu", quantities, {})
        self.assertFalse(result.free_symbols)
        self.assertEqual(result, 100000)


if __name__ == "__main__":
    unittest.main()
