import unittest

from bjt_bias.params import BiasInputs, validate

VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
         "re": "1000", "beta": "150", "vbe": "0.7"}


class TestValidate(unittest.TestCase):
    def test_valid_input_returns_dataclass(self):
        inputs, errors = validate(VALID)
        self.assertEqual(errors, {})
        self.assertIsInstance(inputs, BiasInputs)
        self.assertEqual((inputs.vcc, inputs.beta), (12.0, 150.0))

    def test_blank_field_is_rejected(self):
        inputs, errors = validate({**VALID, "r1": ""})
        self.assertIsNone(inputs)
        self.assertIn("r1", errors)

    def test_non_numeric_is_rejected(self):
        _, errors = validate({**VALID, "rc": "abc"})
        self.assertIn("rc", errors)

    def test_zero_and_negative_resistance_rejected(self):
        for field in ("r1", "r2", "rc", "re"):
            self.assertIn(field, validate({**VALID, field: "0"})[1])
            self.assertIn(field, validate({**VALID, field: "-1"})[1])

    def test_beta_must_be_positive(self):
        self.assertIn("beta", validate({**VALID, "beta": "0"})[1])

    def test_vbe_must_be_below_vcc(self):
        self.assertIn("vbe", validate({**VALID, "vbe": "12"})[1])

    def test_nan_and_inf_rejected(self):
        for value in ("nan", "inf"):
            self.assertIn("vcc", validate({**VALID, "vcc": value})[1])

    def test_missing_key_is_treated_as_blank(self):
        raw = dict(VALID)
        del raw["re"]
        inputs, errors = validate(raw)
        self.assertIsNone(inputs)
        self.assertIn("re", errors)

    def test_whitespace_is_stripped(self):
        inputs, errors = validate({**VALID, "vcc": " 12 "})
        self.assertEqual(errors, {})
        self.assertEqual(inputs.vcc, 12.0)

    def test_beta_between_zero_and_one_is_accepted(self):
        inputs, errors = validate({**VALID, "beta": "0.5"})
        self.assertEqual(errors, {})
        self.assertEqual(inputs.beta, 0.5)


if __name__ == "__main__":
    unittest.main()
