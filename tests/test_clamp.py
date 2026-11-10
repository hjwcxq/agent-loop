import unittest

from calculator import clamp


class ClampTests(unittest.TestCase):
    def test_value_within_range(self):
        self.assertEqual(clamp(5, 1, 10), 5)

    def test_value_below_minimum(self):
        self.assertEqual(clamp(-5, 0, 10), 0)

    def test_value_above_maximum(self):
        self.assertEqual(clamp(15, 0, 10), 10)

    def test_value_equals_minimum(self):
        self.assertEqual(clamp(0, 0, 10), 0)

    def test_value_equals_maximum(self):
        self.assertEqual(clamp(10, 0, 10), 10)

    def test_equal_minimum_and_maximum(self):
        self.assertEqual(clamp(5, 3, 3), 3)
        self.assertEqual(clamp(3, 3, 3), 3)

    def test_negative_bounds(self):
        self.assertEqual(clamp(-10, -5, 0), -5)
        self.assertEqual(clamp(-3, -5, 0), -3)
        self.assertEqual(clamp(2, -5, 0), 0)

    def test_float_values(self):
        self.assertEqual(clamp(1.5, 0.0, 2.0), 1.5)
        self.assertEqual(clamp(-0.5, 0.0, 2.0), 0.0)
        self.assertEqual(clamp(2.5, 0.0, 2.0), 2.0)

    def test_reversed_bounds_raise_value_error(self):
        with self.assertRaises(ValueError):
            clamp(5, 10, 0)


if __name__ == "__main__":
    unittest.main()
