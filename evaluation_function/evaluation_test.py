import unittest

from .evaluation import Params, evaluation_function

REYNOLDS_ANSWER = [
    ["Re", "U*L/nu"],
    ["L", "0.001 m < L < 1 m"],
    ["U", "0.001 m/s < U < 1 m/s"],
    ["nu", "1e-7 m^2/s < nu < 1e-4 m^2/s"],
    ["Re", "Re = U*L/nu"],
]


def reynolds(equation="U*L/nu", L="0.5 m", U="0.2 m/s", nu="1e-6 m^2/s", Re="1e5"):
    return [["Re", equation], ["L", L], ["U", U], ["nu", nu], ["Re", Re]]


class TestEvaluationFunction(unittest.TestCase):
    """Tests for the combined-response evaluation, using the Reynolds number example."""

    def evaluate(self, response, answer=REYNOLDS_ANSWER, params=None):
        return evaluation_function(response, answer, Params(params or {})).to_dict()

    def assertCorrect(self, response, **kwargs):
        result = self.evaluate(response, **kwargs)
        self.assertTrue(result["is_correct"], result["feedback"])

    def assertIncorrect(self, response, feedback_contains, **kwargs):
        result = self.evaluate(response, **kwargs)
        self.assertFalse(result["is_correct"])
        self.assertIn(feedback_contains, result["feedback"])

    def test_all_correct_si(self):
        self.assertCorrect(reynolds())
        self.assertFalse(self.evaluate(reynolds())["feedback"])

    def test_unit_conversion(self):
        # 0.5 m * 0.2 m/s / 1e-6 m^2/s = 1e5
        self.assertCorrect(reynolds(L="50 cm", U="0.72 km/h", nu="0.01 cm^2/s"))

    def test_equivalent_equations(self):
        for equation in ["L*U/nu", "U/(nu/L)", "UL/nu"]:
            with self.subTest(equation=equation):
                self.assertCorrect(reynolds(equation=equation))

    def test_wrong_equation(self):
        self.assertIncorrect(reynolds(equation="U*nu/L"), "Re: the expression is not correct")

    def test_out_of_range_value_is_carried_forward(self):
        result = self.evaluate(reynolds(L="2 m", Re="4e5"))
        self.assertFalse(result["is_correct"])
        self.assertIn("L: the value should be between", result["feedback"])
        self.assertNotIn("follow from your other answers", result["feedback"])

    def test_wrong_units(self):
        self.assertIncorrect(reynolds(U="0.2 m"), "U: the units are not correct")

    def test_missing_units(self):
        self.assertIncorrect(reynolds(U="0.2"), "U: the units are missing")

    def test_computed_tolerance(self):
        self.assertCorrect(reynolds(Re="1.005e5"))
        self.assertIncorrect(reynolds(Re="1.1e5"), "does not follow from your other answers")

    def test_computed_rtol_param(self):
        self.assertCorrect(reynolds(Re="1.1e5"), params={"rtol": 0.2})

    def test_computed_with_units_is_inconsistent(self):
        self.assertIncorrect(reynolds(Re="1e5 m"), "units are not consistent")

    def test_unreadable_quantity_blocks_computed_row(self):
        result = self.evaluate(reynolds(L="abc"))
        self.assertFalse(result["is_correct"])
        self.assertIn("L: Could not read the value", result["feedback"])
        self.assertIn("Re: can't be checked until L can be read", result["feedback"])

    def test_empty_row(self):
        self.assertIncorrect(reynolds(nu=""), "nu: no answer given")

    def test_row_count_mismatch(self):
        self.assertIncorrect(reynolds()[:4], "Expected 5 answers, got 4")

    def test_label_mismatch(self):
        response = reynolds()
        response[1][0] = "X"
        self.assertIncorrect(response, "Row 2 should be 'L'")

    def test_inclusive_bounds(self):
        answer = [["L", "1 m <= L <= 2 m"]]
        self.assertCorrect([["L", "1 m"]], answer=answer)
        self.assertCorrect([["L", "200 cm"]], answer=answer)
        self.assertIncorrect([["L", "1 m"]], "between", answer=[["L", "1 m < L < 2 m"]])

    def test_malformed_answer_raises(self):
        with self.assertRaises(ValueError):
            evaluation_function(reynolds(), "not a list", Params())

    def test_latex_labels(self):
        answer = [[f"${label}$", text] for label, text in REYNOLDS_ANSWER]
        response = [[f"${label}$", text] for label, text in reynolds()]
        self.assertCorrect(response, answer=answer)
        self.assertCorrect(reynolds(), answer=answer)
        self.assertIncorrect(reynolds(U="0.2 m"), "U: the units are not correct", answer=answer)

    def test_dollar_in_answer_raises(self):
        answer = [["$L$", "0.001 m < $L$ < 1 m"]]
        with self.assertRaisesRegex(ValueError, "without '\\$'"):
            evaluation_function([["L", "0.5 m"]], answer, Params())

    def test_range_without_label_raises(self):
        with self.assertRaisesRegex(ValueError, "not between the bounds"):
            evaluation_function([["L", "0.5 m"]], [["L", "0.001 m < l < 1 m"]], Params())

    def test_single_column_rows_with_labels_param(self):
        # A one-column Table response area sends only the cells, with the
        # params client-backend adds alongside the teacher's.
        labels = ["$Re$", "$L$", "$U$", "$nu$", "$Re$"]
        answer = [[text] for _, text in REYNOLDS_ANSWER]
        params = {"labels": labels, "cases": [], "symbols": {}, "submission_context": {}}
        response = [[text] for _, text in reynolds(L="50 cm", U="0.72 km/h", nu="0.01 cm^2/s")]
        self.assertCorrect(response, answer=answer, params=params)
        self.assertIncorrect(
            [[text] for _, text in reynolds(U="0.2 m")], "U: the units are not correct", answer=answer, params=params
        )

    def test_single_column_rows_without_labels_param_raises(self):
        with self.assertRaisesRegex(ValueError, "labels parameter"):
            evaluation_function([["0.5 m"]], [["0.001 m < L < 1 m"]], Params())

    def test_labels_param_count_mismatch_raises(self):
        with self.assertRaisesRegex(ValueError, "1 rows, but 2 labels"):
            evaluation_function([["0.5 m"]], [["0.001 m < L < 1 m"]], Params({"labels": ["L", "U"]}))

    def test_labels_param_must_be_strings(self):
        with self.assertRaisesRegex(ValueError, "list of strings"):
            evaluation_function([["0.5 m"]], [["0.001 m < L < 1 m"]], Params({"labels": "L"}))

    def test_labels_param_keeps_two_column_rows(self):
        self.assertCorrect(reynolds(), params={"labels": ["Re", "L", "U", "nu", "Re"]})

    def test_inequality_response_is_incorrect(self):
        self.assertIncorrect(reynolds(equation="U*L/nu < 3"), "Re: 'U*L/nu < 3' is not an expression")


if __name__ == "__main__":
    unittest.main()
