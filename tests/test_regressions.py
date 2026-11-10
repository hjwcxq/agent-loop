import unittest

from calculator import add


class AddRegressionTests(unittest.TestCase):
    def test_add_negative_and_positive(self):
        self.assertEqual(add(-2, 3), 1)

    def test_add_two_negatives(self):
        self.assertEqual(add(-2, -3), -5)

    def test_add_positive_and_negative(self):
        self.assertEqual(add(2, -3), -1)

    def test_add_mixed_floats(self):
        self.assertEqual(add(-1.5, 0.5), -1.0)

    def test_add_positive_numbers_unchanged(self):
        self.assertEqual(add(2, 3), 5)

    def test_add_zero_unchanged(self):
        self.assertEqual(add(0, 0), 0)


if __name__ == "__main__":
    unittest.main()
