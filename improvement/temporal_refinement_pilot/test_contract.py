import unittest
from fractions import Fraction as F
from contract import floor64, intersection, context_domain, selected, sample_domain


class ContractTests(unittest.TestCase):
    def test_candidate_cannot_expand_or_bridge_gap(self):
        self.assertEqual(intersection([[0, 30]], [[2, 4], [8, 10]]), [[2, 4], [8, 10]])
        self.assertEqual(intersection([[3, 9]], [[2, 4], [8, 10]]), [[3, 4], [8, 9]])
        self.assertEqual(intersection([], [[2, 4]]), [])

    def test_native_fraction_and_half_open_end(self):
        pts = ['0', '1/3', '2/3', '1', '4/3']
        self.assertEqual(sample_domain(pts, F(1, 3), F(1)), [1, 2])
        self.assertTrue(selected([[0, 1]], F(2, 3)))
        self.assertFalse(selected([[0, 1]], F(1)))

    def test_dense_floor_has_real_unique_ordinals(self):
        ids = floor64(100, 1000)
        self.assertEqual((len(ids), ids[0], ids[-1]), (64, 100, 999))
        self.assertEqual(ids, sorted(set(ids)))
        self.assertEqual(floor64(3, 4), [3])
        with self.assertRaises(ValueError):
            floor64(3, 3)

    def test_context_uses_source_offset_once(self):
        self.assertEqual(context_domain([[4, 7], [12, 16]], '90', '120'), (F(91), F(109)))
        self.assertEqual(context_domain([[0, 30]], '90', '120'), (F(90), F(120)))
        self.assertIsNone(context_domain([], '90', '120'))


if __name__ == '__main__':
    unittest.main()
