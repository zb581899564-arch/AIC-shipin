import itertools
from fractions import Fraction
import unittest
from acceptable_program32_math import scan, exact_utility


class Checks(unittest.TestCase):
    def test_better_than_witness_is_not_punished(self):
        r = scan([[6, 9]], [[[3], [9]]], [10], [[0., 2.]], [0], [0], [[6, 3]], chunk=1)
        self.assertEqual(r['loss'], 0.)
        self.assertEqual(r['highest_score_acceptable']['choices'], [1])
        self.assertEqual(r['loss_augmented']['choices'], [1])

    def test_margin_protects_acceptable_MAP(self):
        r = scan([[2, 2]], [[[2], [0]]], [2], [[0., -.25]], [0], [0], [[2, 0]])
        self.assertEqual(r['MAP']['choices'], [0])
        self.assertEqual(r['positive_MAP_regret'], 0.)
        self.assertEqual(r['loss_fraction'], '3/4')
        self.assertEqual(r['loss_augmented']['choices'], [1])

    def test_empty_and_all_acceptable_share_tie(self):
        self.assertEqual(exact_utility(0, [0, 0], [0, 2]), Fraction(1, 2))
        r = scan([[0, 1]], [[[0, 0], [0, 1]]], [0, 2], [[0., 0.]], [1], [1], [[0, 1]])
        self.assertEqual(r['acceptable_programs'], 2)
        self.assertEqual(r['loss'], 0.)
        self.assertEqual(r['highest_score_acceptable']['choices'], r['loss_augmented']['choices'])

    def test_chunk_matches_independent_bruteforce(self):
        lengths = [[0, 2, 3], [0, 1, 2]]
        tp = [[[0, 0], [1, 2], [2, 1]], [[0, 0], [1, 0], [1, 1]]]
        scores = [[-1., -2., -1.5], [-1., -1.25, -1.5]]
        gt = [4, 4]
        witness = [2, 2]
        c = exact_utility(5, [3, 2], gt)
        rows = []
        for a, b in itertools.product(range(3), range(3)):
            p = lengths[0][a] + lengths[1][b]
            t = [tp[0][a][j] + tp[1][b][j] for j in range(2)]
            u = exact_utility(p, t, gt)
            s = Fraction(scores[0][a]) + Fraction(scores[1][b])
            rows.append((u, s, s + max(Fraction(), c-u)))
        expected = max(r[2] for r in rows) - max(r[1] for r in rows if r[0] >= c)
        for chunk in [1, 4, 17]:
            r = scan(lengths, tp, gt, scores, witness, [0, 0], [[0, 0, 0], [0, 0, 0]], chunk=chunk)
            self.assertEqual(Fraction(r['loss_fraction']), expected)
            self.assertEqual(r['acceptable_programs'], sum(u >= c for u, _, _ in rows))


if __name__ == '__main__':
    unittest.main()
