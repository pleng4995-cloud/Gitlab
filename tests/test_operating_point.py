import math
import unittest

from bjt_bias.operating_point import operating_point
from bjt_bias.params import BiasInputs

DEFAULTS = BiasInputs(vcc=12, r1=47000, r2=10000, rc=4700,
                      re=1000, beta=150, vbe=0.7)


class TestOperatingPoint(unittest.TestCase):
    def test_matches_hand_worked_reference(self):
        op = operating_point(DEFAULTS)
        expected = {"vbb": 2.1052631578947367, "rb": 8245.61403508772,
                    "ib": 8.824501487275531e-06, "ic": 0.0013236752230913298,
                    "ie": 0.0013324997245786052, "ve": 1.3324997245786052,
                    "vc": 5.77872645147075, "vce": 4.446226726892145,
                    "vb": 2.032499724578605}
        for key, value in expected.items():
            self.assertTrue(math.isclose(op[key], value, rel_tol=1e-6),
                            f"{key}: {op[key]} != {value}")

    def test_vbe_zero_is_valid_and_active(self):
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 1000, 150, 0.0))
        self.assertGreater(op["ic"], 0)
        self.assertGreater(op["vce"], 0.3)

    def test_cutoff_when_vbe_equals_vbb(self):
        vbb = 12 * 10000 / 57000
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 1000, 150, vbb))
        self.assertEqual(op["ib"], 0)
        self.assertEqual(op["ic"], 0)
        self.assertEqual(op["ie"], 0)
        self.assertEqual(op["ve"], 0)
        self.assertAlmostEqual(op["vb"], vbb, places=9)
        self.assertEqual(op["vce"], 12)

    def test_tiny_re_goes_into_saturation(self):
        op = operating_point(BiasInputs(12, 47000, 10000, 4700, 0.01, 150, 0.7))
        self.assertLess(op["vce"], 0.3)


if __name__ == "__main__":
    unittest.main()
