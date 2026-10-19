import json
import unittest

import numpy as np

from pair_preference_math import (apply_selection, brier, choose_anchor, full_clips,
                                 make_train_pairs, preference_votes, prepare_policy,
                                 select_addition, source_metrics, swapped_distribution)


def ownership(groups, odd_tail=False, counts=None):
    cells = np.arange(2*groups-int(odd_tail), dtype=np.int64)
    n = np.ones(len(cells), dtype=np.int64) if counts is None else np.asarray(counts)
    old = np.repeat(cells, n)
    return old//2, old


def clip(lo, hi):
    return dict(native_start=lo, native_end_exclusive=hi, native_frames=hi-lo)


class DataTests(unittest.TestCase):
    def test_full_clip_fixed_tiling_ranges_and_odd_tail_rejection(self):
        g, old = ownership(8, odd_tail=True)
        clips = full_clips(g, old)
        self.assertEqual(len(clips), 1)
        self.assertEqual(clips[0], dict(start_group=0, end_group_exclusive=4,
                         cell_start=0, cell_end_exclusive=8, native_start=0, native_end_exclusive=8, native_frames=8))
        g, old = ownership(12)
        self.assertEqual([r['start_group'] for r in full_clips(g, old)], [0, 4, 8])

    def test_different_native_lengths_can_have_exact_positive_and_zero_ties(self):
        y = np.zeros((6, 2), bool); y[0, 0] = True; y[2:4, 0] = True
        result = preference_votes(y, clip(0, 2), clip(2, 6))
        self.assertEqual(result['distribution'], [0., 0., 1.])
        self.assertEqual(result['counts'], dict(A=0, B=0, TIE=2))
        self.assertEqual(result['selected_native_counts_A'], [1, 0])
        self.assertEqual(result['selected_native_counts_B'], [2, 0])
        self.assertFalse(result['zero_is_ordinary'])

    def test_rater_disagreement_is_not_tie(self):
        y = np.zeros((4, 10), bool); y[:2, :5] = True; y[2:, 5:] = True
        d = preference_votes(y, clip(0, 2), clip(2, 4))
        self.assertEqual(d['distribution'], [.5, .5, 0.])

    def test_unknowns_and_overlapping_clips_rejected(self):
        for y in (np.array([[1, -1], [0, 1]]), np.array([[True, None], [False, True]], object)):
            with self.assertRaises(ValueError): preference_votes(y, clip(0, 1), clip(1, 2))
        with self.assertRaises(ValueError): preference_votes(np.zeros((5, 2), bool), clip(0, 3), clip(2, 5))

    def test_swap_distribution_involution_and_invalid_values(self):
        p = [.2, .7, .1]
        self.assertEqual(swapped_distribution(p), [.7, .2, .1])
        self.assertEqual(swapped_distribution(swapped_distribution(p)), p)
        for bad in ([.4, .4, .4], [.5, -.1, .6], [np.nan, 0., 1.], [None, 0, 1]):
            with self.assertRaises(ValueError): swapped_distribution(bad)

    def test_pair_strata_quotas_reproducibility_and_correlated_orders(self):
        g, old = ownership(48); clips = full_clips(g, old)
        patterns = [[0, 0, 0, 0], [1, 1, 1, 1], [1, 1, 0, 0], [0, 0, 1, 1]]
        y = np.zeros((len(g), 4), bool)
        for i, c in enumerate(clips): y[c['native_start']:c['native_end_exclusive']] = patterns[i//3]
        first = make_train_pairs('a'*64, clips, y)
        second = make_train_pairs('a'*64, list(reversed(clips)), y)
        self.assertEqual(first, second)
        self.assertEqual(first['selected_strata'], dict(decisive=6, tie=6, disagreement=4))
        self.assertEqual(first['selected_pairs'], 16); self.assertEqual(first['ordered_examples'], 32)
        self.assertEqual(len({r['pair_id'] for r in first['pairs']}), 16)
        self.assertFalse(first['two_orders_are_independent'])
        for row in first['pairs']:
            a, b = row['orders']; self.assertEqual(b['target'], swapped_distribution(a['target']))
            self.assertEqual(a['clip_A'], b['clip_B'])
        json.dumps(first, allow_nan=False)

    def test_missing_strata_backfill_from_all_pool_without_replacement(self):
        g, old = ownership(28); clips = full_clips(g, old); y = np.zeros((len(g), 3), bool)
        d = make_train_pairs('b'*64, clips, y)
        self.assertEqual(d['selected_strata'], dict(decisive=0, tie=16, disagreement=0))
        self.assertEqual(d['available_pairs'], 21)
        short = make_train_pairs('b'*64, clips[:3], y)
        self.assertEqual(short['selected_pairs'], 3)
        with self.assertRaises(ValueError): make_train_pairs('b'*64, clips+[clips[0]], y)


class PolicyTests(unittest.TestCase):
    def test_anchor_longest_run_center_and_earliest_tie(self):
        g, old = ownership(16); base = (g < 7) | ((g >= 8) & (g < 12))
        anchor = choose_anchor(g, old, base)
        # Four-group centers3.5/4.5 are equidistant around the seven-group run.
        self.assertEqual(anchor['anchor']['start_group'], 1)
        self.assertEqual(anchor['longest_baseline_run']['native_frames'], 14)
        equal = (g < 4) | ((g >= 8) & (g < 12))
        self.assertEqual(choose_anchor(g, old, equal)['anchor']['start_group'], 0)

    def test_candidate_overlap_rejected_at_single_native_frame(self):
        g, old = ownership(12); base = g < 4; base[np.flatnonzero(g == 5)[0]] = True
        inventory = prepare_policy(g, old, base)
        self.assertEqual([c['start_group'] for c in inventory['candidates']], [8])
        self.assertEqual([c['start_group'] for c in inventory['overlap_rejected_clips']], [0, 4])

    def test_missing_anchor_abstains_and_does_not_accept_scores(self):
        g, old = ownership(8); base = np.zeros(len(g), bool)
        result = select_addition(g, old, base, [])
        self.assertEqual(result['abstain_reason'], 'NO_COMPLETE_BASELINE_ANCHOR')
        self.assertIsNone(result['selected'])
        with self.assertRaises(ValueError): select_addition(g, old, base, [dict(start_group=0)])

    def test_all_tie_and_probability_equal_half_abstain(self):
        g, old = ownership(8); base = g < 4
        for p in ([0., 0., 1.], [.5, .5, 0.]):
            r = select_addition(g, old, base, [dict(start_group=4, candidate_first=p, anchor_first=p)])
            self.assertEqual(r['abstain_reason'], 'NO_CANDIDATE_WINS_BOTH_ORDERS')
            np.testing.assert_array_equal(apply_selection(base, r), base)

    def test_swap_mapping_wins_both_ties_earlier_and_preserves_baseline(self):
        g, old = ownership(12); base = g < 4; before = base.copy()
        rows = [dict(start_group=s, candidate_first=[.8, .1, .1], anchor_first=[.1, .8, .1]) for s in (4, 8)]
        r = select_addition(g, old, base, rows)
        self.assertEqual(r['selected']['start_group'], 4)
        self.assertEqual(r['selected']['minimum_candidate_probability'], .8)
        proposed = apply_selection(base, r)
        self.assertTrue(proposed[base].all()); self.assertEqual(proposed.sum()-base.sum(), 8)
        np.testing.assert_array_equal(base, before)
        json.dumps(r, allow_nan=False)
        # A fixed first-position bias fails after reverse-order mapping.
        rows[0]['anchor_first'] = [.8, .1, .1]
        self.assertEqual(select_addition(g, old, base, rows)['selected']['start_group'], 8)

    def test_missing_duplicate_or_extraneous_candidate_prediction_rejected(self):
        g, old = ownership(8); base = g < 4
        row = dict(start_group=4, candidate_first=[.8, .1, .1], anchor_first=[.1, .8, .1])
        for rows in ([], [row, row], [dict(row, start_group=5)]):
            with self.assertRaises(ValueError): select_addition(g, old, base, rows)

    def test_all_baseline_preserved_and_mapping_errors_rejected(self):
        g, old = ownership(8); base = np.ones(len(g), bool)
        r = select_addition(g, old, base, [])
        self.assertEqual(r['abstain_reason'], 'NO_DISJOINT_COMPLETE_CANDIDATE')
        np.testing.assert_array_equal(apply_selection(base, r), base)
        with self.assertRaises(ValueError): full_clips(g+1, old)
        with self.assertRaises(ValueError): prepare_policy(g, old, base.astype(int))


class MetricTests(unittest.TestCase):
    def test_source_equal_macro_not_pair_count_and_reverse_mapping(self):
        perfect = dict(target=[1., 0., 0.], first_order=[1., 0., 0.], reverse_order=[0., 1., 0.])
        wrong = dict(target=[1., 0., 0.], first_order=[0., 1., 0.], reverse_order=[1., 0., 0.])
        result = source_metrics({'few': [perfect], 'many': [wrong]*9, 'empty': []})
        self.assertEqual(result['macro']['distribution_brier'], 1.)
        self.assertEqual(result['macro']['swap_total_variation'], 0.)
        self.assertEqual(result['sources_scored'], 2); self.assertEqual(result['sources_without_pairs'], 1)

    def test_both_order_brier_does_not_hide_disagreement_by_averaging(self):
        row = dict(target=[.5, .5, 0.], first_order=[1., 0., 0.], reverse_order=[1., 0., 0.])
        r = source_metrics({'s': [row]})
        self.assertEqual(r['macro']['distribution_brier'], .5)
        self.assertEqual(r['macro']['swap_total_variation'], 1.)

    def test_same_clip_tie_control_and_probability_validation(self):
        row = dict(target=[0., 0., 1.], first_order=[.1, .2, .7], reverse_order=[.2, .1, .7], same_clip=True)
        r = source_metrics({'s': [row]})
        self.assertEqual(r['macro']['same_clip_tie_probability'], .7)
        self.assertEqual(r['macro']['same_clip_tie_strict_argmax_both_fraction'], 1.)
        self.assertAlmostEqual(brier(row['first_order'], row['target']), .14)
        with self.assertRaises(ValueError): source_metrics({'s': [dict(row, target=[1., 0., 0.])]})
        with self.assertRaises(ValueError): brier([np.nan, 0, 1], [0, 0, 1])


if __name__ == '__main__':
    unittest.main()
