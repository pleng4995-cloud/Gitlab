import unittest

from app import _format_current, _format_resistance, _schematic, app

VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
         "re": "1000", "beta": "150", "vbe": "0.7"}

LAB = {"vcc": "12", "r1": "100000", "r2": "22000", "rc": "2200",
       "re": "1000", "beta": "100", "vbe": "0.7"}


class TestFormPage(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_get_returns_form_with_all_fields(self):
        response = self.client.get("/")
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        for field in ("vcc", "r1", "r2", "rc", "re", "beta", "vbe"):
            self.assertIn(f'name="{field}"', body)

    def test_get_prefills_defaults(self):
        body = self.client.get("/").get_data(as_text=True)
        self.assertIn('value="12"', body)
        self.assertIn('value="100000"', body)
        self.assertIn('value="22000"', body)

    def test_no_out_of_scope_features_on_page(self):
        body = self.client.get("/").get_data(as_text=True).lower()
        for word in ("bode", "function generator", "transient", "oscilloscope"):
            self.assertNotIn(word, body)


class TestCompute(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_post_shows_operating_point(self):
        response = self.client.post("/", data=VALID)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("4.446", body)
        self.assertIn("1.324", body)
        self.assertIn("mA", body)
        self.assertIn("active", body)

    def test_invalid_post_keeps_values_and_shows_error(self):
        response = self.client.post("/", data={**VALID, "r1": "0"})
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("ต้องมากกว่า 0", body)
        self.assertIn('value="0"', body)

    def test_cutoff_case_warns(self):
        body = self.client.post("/", data={**VALID, "vbe": "5"}).get_data(as_text=True)
        self.assertIn("cutoff", body)

    def test_saturation_case_warns(self):
        body = self.client.post("/", data={**VALID, "rc": "47000"}).get_data(as_text=True)
        self.assertIn("saturation", body)

    def test_truncated_post_reports_missing_field(self):
        data = {key: value for key, value in VALID.items() if key != "re"}
        response = self.client.post("/", data=data)
        body = response.get_data(as_text=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn("กรุณากรอกตัวเลข", body)

    def test_vcc_change_moves_the_operating_point(self):
        first = self.client.post("/", data=VALID).get_data(as_text=True)
        second = self.client.post("/", data={**VALID, "vcc": "24"}).get_data(as_text=True)
        self.assertIn("4.446", first)
        self.assertIn("5.13", second)
        self.assertNotEqual(first, second)

    def test_vbe_equal_to_vbb_at_route_level_is_cutoff(self):
        body = self.client.post(
            "/", data={**VALID, "vbe": "2.1052631578947367"}
        ).get_data(as_text=True)
        self.assertIn("cutoff", body)


class TestLabReference(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_lab_values_match_independent_reference(self):
        body = self.client.post("/", data=LAB).get_data(as_text=True)
        for expected in ("1.942 V", "1.242 V", "9.294 V", "8.052 V",
                         "12.3 µA", "1.23 mA", "1.242 mA"):
            self.assertIn(expected, body, expected)

    def test_resistance_is_displayed_in_kohm(self):
        self.assertEqual(_format_resistance(100000), "100 kΩ")
        self.assertEqual(_format_resistance(2200), "2.2 kΩ")
        self.assertEqual(_format_resistance(470), "470 Ω")

    def test_schematic_shows_kohm_labels_for_ohm_inputs(self):
        body = self.client.post("/", data=LAB).get_data(as_text=True)
        self.assertIn("100 kΩ", body)
        self.assertIn("22 kΩ", body)
        self.assertIn("2.2 kΩ", body)

    def test_schematic_falls_back_on_non_numeric_values(self):
        labels = _schematic({"vcc": "abc", "r1": "abc", "beta": "abc"})
        self.assertEqual(labels["vcc"], "12 V")
        self.assertEqual(labels["r1"], "100 kΩ")
        self.assertEqual(labels["beta"], "100")
        self.assertTrue(labels["fallback"])

    def test_schematic_falls_back_on_non_finite_and_non_positive_values(self):
        for bad in ("nan", "inf", "1e400", "-100", "0"):
            labels = _schematic({"vcc": bad, "r1": bad, "rc": bad})
            self.assertEqual(labels["vcc"], "12 V", bad)
            self.assertEqual(labels["r1"], "100 kΩ", bad)
            self.assertEqual(labels["rc"], "2.2 kΩ", bad)
            self.assertTrue(labels["fallback"], bad)

    def test_schematic_uses_typed_values_when_they_are_valid(self):
        labels = _schematic({"vcc": "24", "r1": "47000", "r2": "10000",
                             "rc": "4700", "re": "1000", "beta": "150"})
        self.assertEqual(labels["vcc"], "24 V")
        self.assertEqual(labels["r1"], "47 kΩ")
        self.assertFalse(labels["fallback"])

    def test_current_formatter_does_not_show_1000_microamps(self):
        self.assertEqual(_format_current(0.99995e-3), "1 mA")
        self.assertEqual(_format_current(0.999e-3), "999 µA")
        self.assertEqual(_format_current(1e-3), "1 mA")

    def test_active_badge_states_the_correct_threshold(self):
        body = self.client.post("/", data=LAB).get_data(as_text=True)
        self.assertIn("≥ 0.3 V", body)

    def test_saturation_badge_states_the_correct_threshold(self):
        body = self.client.post("/", data={**LAB, "rc": "47000"}).get_data(as_text=True)
        self.assertIn("ต่ำกว่า 0.3 V", body)

    def test_saturation_warning_states_the_approximation(self):
        body = self.client.post("/", data={**LAB, "rc": "47000"}).get_data(as_text=True)
        self.assertIn("forward-active approximation", body)

    def test_cutoff_warning_states_the_approximation(self):
        body = self.client.post("/", data={**LAB, "vbe": "5"}).get_data(as_text=True)
        self.assertIn("forward-active approximation", body)


class TestCrossCheck(unittest.TestCase):
    def setUp(self):
        self.client = app.test_client()

    def test_valid_post_shows_two_methods_and_ok(self):
        body = self.client.post("/", data=VALID).get_data(as_text=True)
        self.assertIn("Nodal", body)
        self.assertIn("OK", body)
        self.assertIn("Δ", body)

    def test_cutoff_shows_not_applicable(self):
        body = self.client.post("/", data={**VALID, "vbe": "5"}).get_data(as_text=True)
        self.assertIn("n/a", body)


if __name__ == "__main__":
    unittest.main()
