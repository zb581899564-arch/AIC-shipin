"""Independent PTS-count oracle, including the actual failed 12fps output."""
import json
import unittest
from fractions import Fraction as F
from native_grammar import NativeSegmentsGrammar


class NativeGrammarTests(unittest.TestCase):
    def test_actual_failure(self):
        points = [F(i, 12) for i in range(1800)]
        grammar = NativeSegmentsGrammar(30, points, F(28))
        failed = '{"segments":[[0.0,0.0333],[0.0667,0.1333],[0.1667,0.2333],[0.2667,0.3333],[0.3667,0.4333]]}'
        self.assertFalse(grammar.complete(failed))
        self.assertFalse(grammar.valid_prefix('{"segments":[[0.1667,0.2333]'))

    def test_complete_against_independent_oracle(self):
        points = [F(0), F(1, 12), F(1, 5), F(7, 20), F(9, 10)]
        grammar = NativeSegmentsGrammar(1, points, F(0))
        tested = 0
        for a in range(101):
            for b in range(a+1, 101):
                start, end = F(a, 100), F(b, 100)
                text = json.dumps({'segments': [[a/100, b/100]]}, separators=(',', ':'))
                expected = any(start <= p < end for p in points)
                self.assertEqual(grammar.complete(text), expected, text)
                if expected:
                    self.assertTrue(all(grammar.valid_prefix(text[:k]) for k in range(len(text)+1)))
                tested += 1
        self.assertEqual(tested, 5050)

    def test_offset_nonzero_and_vfr(self):
        grammar = NativeSegmentsGrammar(F(3, 2), ['10', '101/10', '21/2', '57/5'], F(10))
        self.assertTrue(grammar.complete('{"segments":[[0.09,0.11],[0.49,0.51]]}'))
        self.assertFalse(grammar.complete('{"segments":[[0.11,0.49]]}'))
        self.assertTrue(grammar.complete('{"segments":[]}'))
        self.assertFalse(grammar.complete('{"segments":[[1.4,1.4]]}'))

    def test_sorted_count_and_no_fabricated_end_frame(self):
        g = NativeSegmentsGrammar(1, ['0','1/3','2/3','1'], F(0))
        self.assertFalse(g.complete('{"segments":[[0.9,1]]}'))
        self.assertFalse(g.complete('{"segments":[[0,0.5],[0.4,1]]}'))
        self.assertFalse(g.complete('{"segments":[[0,1],[1,1.1]]}'))
        with self.assertRaises(ValueError):
            NativeSegmentsGrammar(1, ['1','2'], F(0))


if __name__ == '__main__':
    unittest.main()
