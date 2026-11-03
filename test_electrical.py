import unittest
from electrical import analyze_circuit, analyze_dc


class TestDCAnalyzer(unittest.TestCase):
    def test_known_values(self):
        result = analyze_dc(12, 6)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)

    def test_zero_voltage(self):
        result = analyze_dc(0, 10)
        self.assertAlmostEqual(result["current_a"], 0.0)
        self.assertAlmostEqual(result["power_w"], 0.0)

    def test_mixed_series_parallel_circuit(self):
        circuit = {
            "type": "series",
            "components": [
                {"name": "R1", "resistance_ohm": 4},
                {
                    "type": "parallel",
                    "components": [
                        {"name": "R2", "resistance_ohm": 6},
                        {"name": "R3", "resistance_ohm": 3},
                    ],
                },
            ],
        }

        result = analyze_circuit(12, circuit)

        self.assertAlmostEqual(result["total_resistance_ohm"], 6.0)
        self.assertAlmostEqual(result["current_a"], 2.0)
        self.assertAlmostEqual(result["power_w"], 24.0)
        self.assertAlmostEqual(result["components"][0]["voltage_v"], 8.0)
        self.assertAlmostEqual(result["components"][1]["current_a"], 2 / 3)
        self.assertAlmostEqual(result["components"][2]["current_a"], 4 / 3)

    def test_zero_resistance_is_rejected(self):
        with self.assertRaises(ValueError):
            analyze_dc(12, 0)


if __name__ == "__main__":
    unittest.main()