"""Recipe unit-nodeps: stdlib unittest, for a project with no dependencies. pytest runs this file too.

Run without pytest: python3 -m unittest discover -s recipes/python/unit-nodeps
"""
import unittest

from slug import slugify


class SlugifyTest(unittest.TestCase):
    def test_table(self):
        cases = [
            ("Hello, World!", "hello-world"),
            ("  spaces  around ", "spaces-around"),
            ("Crème brûlée", "creme-brulee"),
            ("", ""),
        ]
        for text, expected in cases:
            with self.subTest(text=text):  # each row reports on its own
                self.assertEqual(slugify(text), expected)


if __name__ == "__main__":
    unittest.main()
