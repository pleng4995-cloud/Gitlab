import unittest

from bjt_bias.regions import classify

ACTIVE = {"ib": 1e-5, "vce": 4.4}
SATURATED = {"ib": 1e-5, "vce": 0.2}
BOUNDARY = {"ib": 1e-5, "vce": 0.3}
OFF = {"ib": 0.0, "vce": 12.0}


class TestClassify(unittest.TestCase):
    def test_active_has_no_warning(self):
        region, warnings = classify(ACTIVE)
        self.assertEqual(region, "active")
        self.assertEqual(warnings, [])

    def test_saturation_below_threshold(self):
        region, warnings = classify(SATURATED)
        self.assertEqual(region, "saturation")
        self.assertEqual(len(warnings), 1)

    def test_exactly_0_3_v_is_active(self):
        self.assertEqual(classify(BOUNDARY)[0], "active")

    def test_zero_base_current_is_cutoff(self):
        region, warnings = classify(OFF)
        self.assertEqual(region, "cutoff")
        self.assertEqual(len(warnings), 1)


if __name__ == "__main__":
    unittest.main()
