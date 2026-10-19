"""Targeted synthetic pure-function checks; no historical data/model access."""
from fractions import Fraction as F
import unittest

from branch_evaluate import (deduplicate_candidates, evaluate_source, native_frames,
                             pairwise_concordance, score_proposal, select_candidate)


def candidate(event, interval, margin, roles=('overlap',)):
    return dict(event_id=event, case_id=event+'.verify', interval_exact=interval,
                M_KEEP=margin, view_roles=list(roles))


class BranchEvaluateTest(unittest.TestCase):
    def test_alias_fixed_before_scores_and_zero_contributions_omitted(self):
        pts = list(map(F, range(5)))
        candidates = [candidate('z', [1, 2], 100), candidate('a', [1, 2], -1),
                      candidate('covered', [0, 1], 1000), candidate('base', [3, 4], 1000, ('baseline',))]
        unique, inventory = deduplicate_candidates(candidates, [[0, 1]], pts)
        self.assertEqual([c['event_id'] for c in unique], ['a'])
        self.assertIsNone(select_candidate(unique))
        self.assertEqual(inventory['zero_new_native_candidates'], 1)
        self.assertEqual(inventory['non_overlap_candidates'], 1)
        self.assertEqual(inventory['native_aliases'], [{'event_id': 'z', 'canonical_event_id': 'a'}])

    def test_one_positive_candidate_maximum_and_event_tie(self):
        candidates = [candidate('b', [1, 2], 2), candidate('a', [2, 3], 2), candidate('z', [3, 4], 1)]
        self.assertEqual(select_candidate(candidates)['event_id'], 'a')
        self.assertIsNone(select_candidate([candidate('zero', [0, 1], 0)]))

    def test_exact_union_f1_and_all_rater_recall(self):
        refs = [[[0, 2]]]*5 + [[[1, 3]]]*5
        result = score_proposal([[0, 2], [1, 3]], refs)
        self.assertEqual(result['selected_duration']['exact'], '3')
        self.assertEqual(result['f1']['exact'], '4/5')
        self.assertEqual(len(result['per_rater']), 10)
        self.assertTrue(all(row['recall']['exact'] == '1' for row in result['per_rater']))

    def test_empty_has_no_fabricated_perfect_f1(self):
        self.assertEqual(score_proposal([], [[]]*10)['f1']['exact'], '0')
        with self.assertRaises(ValueError):
            score_proposal([], [[]]*9)

    def test_native_vfr_half_open_mapping(self):
        pts = [F(0), F(1, 10), F(3, 5), F(7, 10)]
        self.assertEqual(native_frames([['1/10', '7/10']], pts), frozenset((1, 2)))

    def test_concordance_uses_utilities_not_threshold_and_ties_half(self):
        rows = [dict(M_KEEP=-10., marginal_f1_exact='0'), dict(M_KEEP=-1., marginal_f1_exact='1/10'),
                dict(M_KEEP=-1., marginal_f1_exact='1/5')]
        result = pairwise_concordance(rows)
        self.assertEqual(result['informative_pairs'], 3)
        self.assertEqual(result['margin_tied_pairs'], 1)
        self.assertEqual(result['concordance']['exact'], '5/6')
        self.assertIsNone(pairwise_concordance([rows[0]])['concordance'])

    def test_fixed_baseline_preserved_and_old_metrics_only_referenced(self):
        saved = dict(video_id='s', baseline_spans=[[0, 1]], augmented_spans=[[0, 2]],
                     baseline_selected_frames=1, augmented_selected_frames=2,
                     baseline={k: {'exact': '1/2', 'value': .5} for k in ('f1', 'recall', 'precision')},
                     augmented={k: {'exact': '2/3', 'value': 2/3} for k in ('f1', 'recall', 'precision')})
        result = evaluate_source(saved, [candidate('x', [2, 3], 1)], list(map(F, range(4))), [[[0, 3]]]*10)
        self.assertEqual(result['proposal_spans'], [['0', '1'], ['2', '3']])
        self.assertEqual(result['new_native_frames'], 1)
        self.assertTrue(result['baseline_native_frames_preserved'])
        self.assertEqual(result['saved_baseline'], saved['baseline'])
        self.assertFalse(result['old_aggregate_metrics_recomputed'])
        self.assertEqual(result['delta_f1_vs_saved_baseline']['exact'], '3/10')
        self.assertEqual(result['versus_old_hard_KEEP']['added_native_frames'], 1)
        self.assertEqual(result['versus_old_hard_KEEP']['removed_native_frames'], 1)

    def test_invalid_margin_and_duplicate_event_fail(self):
        with self.assertRaises(ValueError):
            select_candidate([candidate('bad', [0, 1], float('nan'))])
        with self.assertRaises(ValueError):
            deduplicate_candidates([candidate('same', [0, 1], 1)]*2, [], [F(0), F(1)])


if __name__ == '__main__':
    unittest.main()
