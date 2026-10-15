"""Regression tests for a native endpoint beyond the frozen field and invalid field holes."""
import unittest
from fractions import Fraction as F
from source_domain import source_domains, window_context


class DomainTests(unittest.TestCase):
    def test_native_endpoint_roundtrip_is_uniformly_bounded(self):
        field = [{'video_id': 'example', 'source_frame': i} for i in range(9)]
        domain = source_domains(field, {'example'})['example']
        pts = [str(F(i, 60)) for i in range(10)]
        window = {'all_source_exact_pts': pts, 'exact_raw_start': '0',
                  'exact_raw_end': '15000000000000001/100000000000000000',
                  'eligible_first': 0, 'eligible_stop': 10}
        core, context = window_context(window, [[0.10, 0.14]], domain)
        self.assertEqual(core, {6, 7, 8})
        self.assertEqual(context, set(range(9)))
        self.assertTrue(F(pts[9]) < F(window['exact_raw_end']))
        self.assertNotIn(9, context)

    def test_holes_and_duplicates_stop(self):
        for ids in ([0, 2], [0, 1, 1]):
            with self.subTest(ids=ids), self.assertRaises(ValueError):
                source_domains([{'video_id': 'a', 'source_frame': i} for i in ids], {'a'})

    def test_missing_source_stops(self):
        with self.assertRaises(ValueError):
            source_domains([{'video_id': 'a', 'source_frame': 0}], {'a', 'b'})

    def test_empty_and_core_outside_domain(self):
        w = {'all_source_exact_pts': ['0', '1', '2'], 'exact_raw_start': '0',
             'exact_raw_end': '3', 'eligible_first': 0, 'eligible_stop': 3}
        self.assertEqual(window_context(w, [], (0, 2)), (set(), set()))
        with self.assertRaises(ValueError):
            window_context(w, [[2, 3]], (0, 2))


if __name__ == '__main__':
    unittest.main()
