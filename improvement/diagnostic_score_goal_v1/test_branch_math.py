import math
import unittest

from branch_math import (CANONICAL_RESPONSES, build_teacher_forced_sequence,
                         summarize_branch_log_probs, validate_branch_token_ids)


class BranchMathTest(unittest.TestCase):
    def test_exact_canonical_responses(self):
        self.assertEqual(CANONICAL_RESPONSES, {
            'KEEP': '{"decision":"KEEP"}',
            'UNKNOWN': '{"decision":"UNKNOWN"}',
            'DROP': '{"decision":"DROP"}',
        })

    def test_shifted_positions_predict_answer_including_last_token(self):
        prefix, answer = [11, 12, 13], [21, 22, 23]
        result = build_teacher_forced_sequence(prefix, answer)
        self.assertEqual(result['input_ids'], [11, 12, 13, 21, 22])
        self.assertEqual(result['labels'], answer)
        self.assertEqual(result['logit_positions'], [2, 3, 4])
        self.assertEqual(result['prefix_length'], 3)
        result['input_ids'][0] = 0
        result['labels'][0] = 0
        self.assertEqual(prefix, [11, 12, 13])
        self.assertEqual(answer, [21, 22, 23])

    def test_single_answer_token_uses_last_prefix_logit(self):
        self.assertEqual(build_teacher_forced_sequence([8], [9]), {
            'input_ids': [8], 'labels': [9], 'logit_positions': [0], 'prefix_length': 1,
        })

    def test_invalid_or_empty_token_ids_rejected(self):
        for bad in ([], [True], [-1], [1.5], ['2']):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    build_teacher_forced_sequence(bad, [2])
                with self.assertRaises(ValueError):
                    build_teacher_forced_sequence([2], bad)

    def test_distinct_branch_id_validation(self):
        ids = {'KEEP': [1, 2], 'UNKNOWN': [1, 3], 'DROP': [1, 4]}
        copy = validate_branch_token_ids(ids)
        copy['KEEP'][0] = 9
        self.assertEqual(ids['KEEP'], [1, 2])
        ids['DROP'] = [1, 2]
        with self.assertRaises(ValueError):
            validate_branch_token_ids(ids)

    def test_complete_sequence_sum_not_length_average(self):
        result = summarize_branch_log_probs({'KEEP': [-.2, -.3], 'UNKNOWN': [-.4], 'DROP': [-.7]})
        self.assertEqual(result['sequence_log_probs'], {'KEEP': -.5, 'UNKNOWN': -.4, 'DROP': -.7})
        self.assertGreater(result['probabilities']['UNKNOWN'], result['probabilities']['KEEP'])
        self.assertAlmostEqual(sum(result['probabilities'].values()), 1.)
        self.assertAlmostEqual(result['M_KEEP'], -.5 - math.log(math.exp(-.4) + math.exp(-.7)))

    def test_unknown_changes_both_margins(self):
        low = summarize_branch_log_probs({'KEEP': [-1.], 'UNKNOWN': [-10.], 'DROP': [-2.]})
        high = summarize_branch_log_probs({'KEEP': [-1.], 'UNKNOWN': [-.1], 'DROP': [-2.]})
        self.assertLess(high['M_KEEP'], low['M_KEEP'])
        self.assertLess(high['M_DROP'], low['M_DROP'])
        self.assertGreater(high['probabilities']['UNKNOWN'], low['probabilities']['UNKNOWN'])

    def test_extreme_logits_stay_stable(self):
        result = summarize_branch_log_probs({'KEEP': [0.], 'UNKNOWN': [-10000.], 'DROP': [-20000.]})
        self.assertEqual(result['probabilities']['KEEP'], 1.)
        self.assertEqual(result['M_KEEP'], 10000.)
        self.assertEqual(result['M_DROP'], -20000.)
        self.assertTrue(all(math.isfinite(v) for v in result['probabilities'].values()))

    def test_huge_common_negative_shift_preserves_three_way_normalization(self):
        result = summarize_branch_log_probs({name: [-1e300] for name in CANONICAL_RESPONSES})
        for probability in result['probabilities'].values():
            self.assertAlmostEqual(probability, 1. / 3.)
        self.assertAlmostEqual(result['M_KEEP'], -math.log(2.))
        self.assertAlmostEqual(result['M_DROP'], -math.log(2.))

    def test_nonfinite_positive_bool_and_overflow_rejected(self):
        for bad in ([math.nan], [math.inf], [-math.inf], [.1], [True], [-1e308, -1e308], []):
            with self.subTest(bad=bad):
                with self.assertRaises(ValueError):
                    summarize_branch_log_probs({'KEEP': bad, 'UNKNOWN': [-1.], 'DROP': [-2.]})

    def test_missing_or_extra_branch_rejected(self):
        for bad in ({'KEEP': [-1.], 'DROP': [-2.]},
                    {'KEEP': [-1.], 'UNKNOWN': [-2.], 'DROP': [-3.], 'OTHER': [-4.]}):
            with self.assertRaises(ValueError):
                summarize_branch_log_probs(bad)


if __name__ == '__main__':
    unittest.main()
