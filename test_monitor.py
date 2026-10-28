#!/usr/bin/env python3
"""Tests for the diff logic. Runs offline on fixtures - no network.

python -m unittest -v
"""
import unittest

from monitor import diff

A = "https://books.toscrape.com/catalogue/a_1/index.html"
B = "https://books.toscrape.com/catalogue/b_2/index.html"
C = "https://books.toscrape.com/catalogue/c_3/index.html"


class DiffTests(unittest.TestCase):
    def test_first_run_marks_everything_new(self):
        rows = diff({}, {A: {"title": "A", "price": 10.0}})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["change"], "NEW")

    def test_price_move_is_detected(self):
        rows = diff({A: {"title": "A", "price": 10.0}}, {A: {"title": "A", "price": 12.5}})
        self.assertEqual(rows[0]["change"], "PRICE")
        self.assertEqual(rows[0]["old_price"], "10.00")
        self.assertEqual(rows[0]["new_price"], "12.50")

    def test_no_change_produces_no_rows(self):
        snap = {A: {"title": "A", "price": 10.0}}
        self.assertEqual(diff(snap, snap), [])

    def test_removed_item_is_reported(self):
        rows = diff({A: {"title": "A", "price": 10.0}, B: {"title": "B", "price": 5.0}},
                    {A: {"title": "A", "price": 10.0}})
        self.assertEqual(len(rows), 1)
        self.assertEqual(rows[0]["change"], "GONE")
        self.assertEqual(rows[0]["title"], "B")

    def test_mixed_run_counts(self):
        old = {A: {"title": "A", "price": 10.0}, B: {"title": "B", "price": 5.0}}
        new = {A: {"title": "A", "price": 9.0}, C: {"title": "C", "price": 7.0}}
        rows = diff(old, new)
        kinds = sorted(r["change"] for r in rows)
        self.assertEqual(kinds, ["GONE", "NEW", "PRICE"])

    def test_tiny_float_noise_is_not_a_change(self):
        rows = diff({A: {"title": "A", "price": 10.0}}, {A: {"title": "A", "price": 10.0004}})
        self.assertEqual(rows, [])


if __name__ == "__main__":
    unittest.main()
