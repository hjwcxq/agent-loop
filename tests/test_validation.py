import unittest

from calculator import divide, percentage


class DivideValidationTests(unittest.TestCase):
    def test_divide_by_negative_denominator(self):
        self.assertEqual(divide(9, -3), -3)
        self.assertEqual(divide(-9, -3), 3)

    def test_divide_by_zero_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "^除数不能为零$"):
            divide(1, 0)


class PercentageValidationTests(unittest.TestCase):
    def test_percentage_with_negative_denominator(self):
        self.assertEqual(percentage(3, -12), -25)
        self.assertEqual(percentage(-3, -12), 25)

    def test_percentage_with_zero_denominator_raises_value_error(self):
        with self.assertRaisesRegex(ValueError, "^除数不能为零$"):
            percentage(1, 0)


if __name__ == "__main__":
    unittest.main()
