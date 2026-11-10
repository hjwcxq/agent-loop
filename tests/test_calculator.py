import unittest

from calculator import add, divide, multiply, percentage, subtract


class CalculatorBaselineTests(unittest.TestCase):
    def test_add_positive_numbers(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_zero(self):
        self.assertEqual(add(0, 0), 0)

    def test_subtract(self):
        self.assertEqual(subtract(2, 3), -1)

    def test_multiply(self):
        self.assertEqual(multiply(-2, 3), -6)

    def test_divide(self):
        self.assertEqual(divide(9, 2), 4.5)

    def test_divide_negative(self):
        self.assertEqual(divide(-9, 2), -4.5)

    def test_divide_by_zero(self):
        with self.assertRaisesRegex(ValueError, "^除数不能为零$"):
            divide(1, 0)

    def test_percentage(self):
        self.assertEqual(percentage(3, 12), 25)

    def test_percentage_zero(self):
        self.assertEqual(percentage(0, 12), 0)

    def test_percentage_divide_by_zero(self):
        with self.assertRaisesRegex(ValueError, "^除数不能为零$"):
            percentage(1, 0)


if __name__ == "__main__":
    unittest.main()
