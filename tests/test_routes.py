import unittest

from app import app

VALID = {"vcc": "12", "r1": "47000", "r2": "10000", "rc": "4700",
         "re": "1000", "beta": "150", "vbe": "0.7"}


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
        self.assertIn('value="47000"', body)

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
