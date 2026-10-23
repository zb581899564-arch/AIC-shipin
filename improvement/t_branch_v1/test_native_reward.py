"""Targeted hand-checks for native provenance, references and UNKNOWN isolation."""
from fractions import Fraction
import unittest

import numpy as np

from native_sets import NativeTimeline, accepted_selection, replace_component
from preference_reward import SummaryReview, Unscorable, explicit_highlight_metrics, source_marginal_gain, summary_agreement


def mask(size, indices):
    result = np.zeros(size, dtype=bool)
    result[list(indices)] = True
    return result


class NativeRewardTests(unittest.TestCase):
    def test_irregular_native_pts_and_overlap(self):
        timeline = NativeTimeline((Fraction(0), Fraction(1, 10), Fraction(3, 10), Fraction(4, 10)), Fraction(1, 2))
        result = timeline.intervals([('0.1', '0.4'), ('0.3', '0.5')])
        self.assertEqual(np.flatnonzero(result).tolist(), [1, 2, 3])

    def test_original_clock_origin(self):
        timeline = NativeTimeline.from_clock(dict(PTS=['5', '51/10'], first_PTS_exact='5',
                                                  physical_end_exact='26/5', native_frames=2))
        self.assertEqual(timeline.points, (Fraction(0), Fraction(1, 10)))
        self.assertEqual(timeline.end, Fraction(1, 5))

    def test_no_endpoint_or_frame_repair(self):
        timeline = NativeTimeline((Fraction(0), Fraction(1)), Fraction(2))
        with self.assertRaises(ValueError):
            timeline.intervals([(0, '2.001')])
        with self.assertRaises(ValueError):
            NativeTimeline.from_clock(dict(PTS=['0'], first_PTS_exact='0', physical_end_exact='1', native_frames=2))

    def test_overlap_keeps_other_window_contribution(self):
        components = dict(a=mask(6, [1, 2, 3]), b=mask(6, [3, 4]))
        result = replace_component(components, 'a', mask(6, []), mask(6, [0, 1, 2, 3]))
        self.assertEqual(np.flatnonzero(result).tolist(), [3, 4])
        self.assertEqual(np.flatnonzero(components['a']).tolist(), [1, 2, 3])

    def test_replacement_cannot_leave_window(self):
        with self.assertRaises(ValueError):
            replace_component(dict(a=mask(6, [1])), 'a', mask(6, [5]), mask(6, [0, 1]))

    def test_success_empty_and_failed_are_different(self):
        self.assertFalse(accepted_selection('LEGAL_EMPTY', mask(4, []), 4).any())
        for state, result in [('FAILED', None), ('MODEL_OK', mask(4, [])), ('LEGAL_EMPTY', mask(4, [1]))]:
            with self.assertRaises(ValueError):
                accepted_selection(state, result, 4)

    def test_no_padding_or_implicit_boolean_cast(self):
        with self.assertRaises(ValueError):
            accepted_selection('MODEL_OK', np.array([0, 1]), 4)

    def test_all_raters_average_not_best_rater(self):
        observed = np.ones(4, dtype=bool)
        reviews = [SummaryReview('a', mask(4, [1]), observed), SummaryReview('b', mask(4, [2]), observed)]
        result = summary_agreement(mask(4, [1]), reviews, 2)
        self.assertEqual(result['mean_f1'], 0.5)
        self.assertEqual(result['unselected_summary_semantic_label'], 'UNKNOWN')
        with self.assertRaises(ValueError):
            summary_agreement(mask(4, [1]), reviews[:1], 2)

    def test_unknown_never_becomes_ordinary(self):
        labels = np.array([-1, 1, 1, 0, -1], dtype=np.int8)
        first = explicit_highlight_metrics(mask(5, [0, 1]), labels, 'EXPLICIT_HL_NHL_UNKNOWN')
        second = explicit_highlight_metrics(mask(5, [1, 4]), labels, 'EXPLICIT_HL_NHL_UNKNOWN')
        self.assertAlmostEqual(first['f1'], 2 / 3)
        self.assertEqual(first['f1'], second['f1'])
        with self.assertRaises(ValueError):
            explicit_highlight_metrics(mask(5, [1]), labels, 'SUMMARY_UNSELECTED')

    def test_unobserved_domain_is_unscorable(self):
        with self.assertRaises(Unscorable):
            explicit_highlight_metrics(mask(4, []), np.full(4, -1, dtype=np.int8), 'EXPLICIT_HL_NHL_UNKNOWN')

    def test_source_marginal_not_isolated_window_f1(self):
        components = dict(a=mask(6, [0]), b=mask(6, [3, 4]))
        reviews = [SummaryReview('r', mask(6, [1, 3]), np.ones(6, dtype=bool))]
        result = source_marginal_gain(components, 'a', mask(6, [1]), mask(6, [0, 1, 2]), reviews, 1)
        self.assertAlmostEqual(result['anchor']['mean_f1'], 2 / 5)
        self.assertAlmostEqual(result['candidate']['mean_f1'], 4 / 5)
        self.assertAlmostEqual(result['delta_f1'], 2 / 5)


if __name__ == '__main__':
    unittest.main()
