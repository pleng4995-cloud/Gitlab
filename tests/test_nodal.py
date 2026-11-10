import inspect
import math
import unittest

from bjt_bias import nodal
from bjt_bias.nodal import nodal_operating_point
from bjt_bias.operating_point import operating_point
from bjt_bias.params import BiasInputs

CASES = [
    BiasInputs(12, 47000, 10000, 4700, 1000, 150, 0.7),
    BiasInputs(24, 47000, 10000, 4700, 1000, 150, 0.7),
    BiasInputs(12, 10000, 47000, 2200, 470, 100, 0.65),
]


class TestNodal(unittest.TestCase):
    def test_matches_hand_worked_reference(self):
        op = nodal_operating_point(CASES[0])
        expected = {"ib": 8.824501487275531e-06, "ic": 0.0013236752230913298,
                    "ie": 0.0013324997245786052, "vb": 2.032499724578605,
                    "vc": 5.77872645147075, "ve": 1.3324997245786052,
                    "vce": 4.446226726892145}
        for key, value in expected.items():
            self.assertTrue(math.isclose(op[key], value, rel_tol=1e-6),
                            f"{key}: {op[key]} != {value}")

    def test_agrees_with_closed_form(self):
        for case in CASES:
            nodal_op = nodal_operating_point(case)
            closed_op = operating_point(case)
            for key in ("ib", "ic", "ie", "vb", "vc", "ve", "vce"):
                self.assertTrue(math.isclose(nodal_op[key], closed_op[key], rel_tol=1e-9),
                                f"{key} differs on {case}")

    def test_solver_swaps_rows_when_pivot_is_zero(self):
        self.assertEqual(nodal._solve([[0, 1], [1, 0]], [2, 3]), [3, 2])

    def test_does_not_import_closed_form_module(self):
        source = inspect.getsource(nodal)
        self.assertNotIn("from .operating_point", source)
        self.assertNotIn("from bjt_bias.operating_point", source)
        self.assertNotIn("import operating_point", source)


if __name__ == "__main__":
    unittest.main()
