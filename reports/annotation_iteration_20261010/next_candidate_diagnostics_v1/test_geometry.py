"""Independent exhaustive integer-position oracle and rejection checks."""
from fractions import Fraction as F
import random
import unittest
from geometry_diagnostic import best_maximum_box, maximum_box, metrics, number


def oracle(width, height, ratio, reference):
    a, b = ratio
    w = min(width, height*a//b)
    h = F(w*b, a)
    rx, ry, rw, rh = reference
    scores = []
    for x in range(width-w+1):
        for y in range(int(F(height)-h)+1):
            iw = max(F(0), min(x+w, rx+rw)-max(x, rx))
            ih = max(F(0), min(y+h, ry+rh)-max(y, ry))
            common = iw*ih
            scores.append(common/(w*h+rw*rh-common))
    return min(scores), max(scores)


class GeometryTests(unittest.TestCase):
    def test_exact_breakpoints_match_exhaustive_oracle(self):
        rng = random.Random(20261010)
        for _ in range(160):
            W, H = rng.randint(4, 25), rng.randint(4, 25)
            ratio = rng.choice([(16, 9), (9, 16), (1, 1), (3, 2)])
            w, h = F(rng.randint(1, W*4), 4), F(rng.randint(1, H*4), 4)
            x, y = F(rng.randint(0, int((W-w)*4)), 4), F(rng.randint(0, int((H-h)*4)), 4)
            ref = (x, y, w, h)
            low, high = oracle(W, H, ratio, ref)
            self.assertEqual(best_maximum_box(W, H, ratio, ref)[0], high)
            self.assertEqual(F(metrics(W,H,ratio,ref)['worst_position_maxwidth_iou']['exact']),low)

    def test_containment_upper_bound_and_center_gap(self):
        m = metrics(100, 100, (1, 1), (20, 20, 20, 20), (0, 0, 100, 100))
        self.assertEqual(m['best_position_maxwidth_iou']['exact'], '1/25')
        self.assertEqual(m['center_gap']['exact'], '0')
        self.assertIsNone(metrics(100, 100, (1, 1), (20, 20, 20, 20))['actual_iou'])

    def test_rejects_invalid_geometry(self):
        for ref in [(0, 0, 0, 2), (-1, 0, 2, 2), (0, 0, 21, 2), (0, 0, 2, 21)]:
            with self.assertRaises(ValueError):
                metrics(20, 20, (1, 1), ref)
        for bad in [float('nan'), float('inf'), True]:
            with self.assertRaises(ValueError):
                number(bad)
        with self.assertRaises(ValueError):
            maximum_box(10.5, 10, (1, 1))
        with self.assertRaises(ValueError):
            metrics(20, 20, (1, 1), (1, 1, 10, 10), (0, 0, 10, 10))


if __name__ == '__main__':
    unittest.main()
