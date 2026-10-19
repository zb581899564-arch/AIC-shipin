import copy
import json
import unittest

import numpy as np
import torch

from context_review_v29 import (compare_predictions, prefix_differences, select_pilot_targets,
                                validate_alias, validate_raw)


def fixture():
    sources = ['S'+str(i) for i in range(5)]
    generic, controls = [], []
    for sid in sources:
        for j in range(4):
            generic.append(dict(source_id=sid, purpose='FIXED_GENERIC_PAIR', first_id=sid+'_'+str(j)+'AB',
                                reverse_id=sid+'_'+str(j)+'BA', target=[.7, .1, .2], same_clip=False))
        controls.append(dict(source_id=sid, purpose='IDENTICAL_CLIP_TIE_CONTROL', first_id=sid+'_SELF',
                             reverse_id=sid+'_SELF', target=[0., 0., 1.], same_clip=True))
    choices = {'OLD_BASE_LOCAL': [.2, .6, .2], 'OLD_PAIR_LOCAL': [.4, .3, .3], 'BASE_TRUE': [.65, .15, .2],
               'TRAIN_SOURCE_EQUAL_PRIOR': [.27, .27, .46], 'PAIR_TRUE': [.7, .1, .2], 'PAIR_FOREIGN': [.45, .3, .25]}
    predictions = {}
    for name, p in choices.items():
        scores = {}
        for row in generic:
            scores[row['first_id']] = list(p)
            scores[row['reverse_id']] = [p[1], p[0], p[2]]
        if name != 'PAIR_FOREIGN':
            for row in controls: scores[row['first_id']] = [.1, .1, .8]
        predictions[name] = scores
    return sources, generic, controls, predictions


class ComparisonTests(unittest.TestCase):
    def test_all_frozen_checks_pass_without_production_qualification(self):
        sources, generic, controls, scores = fixture()
        result = compare_predictions(generic, controls, scores, sources)
        self.assertTrue(all(result['checks'].values()))
        self.assertTrue(result['remaining_TRUE_pair_admitted'])
        self.assertFalse(result['production_prepare_approved'])
        self.assertEqual(result['primary_role'], 'PAIR_TRUE')
        self.assertAlmostEqual(result['metrics']['PAIR_TRUE']['generic']['macro']['distribution_brier'], 0.)
        self.assertAlmostEqual(result['metrics']['PAIR_TRUE']['generic']['macro']['swap_total_variation'], 0.)
        self.assertEqual(result['metrics']['PAIR_TRUE']['self']['sources_with_same_clip_controls'], 5)
        # Consistent AB/BA class flips are not mistaken for within-source content variation.
        self.assertTrue(all(r['constant_within_source'] for r in result['metrics']['PAIR_TRUE']['nonconstant_behavior'].values()))
        json.dumps(result, allow_nan=False)

    def test_better_BASE_cannot_rescue_failed_fixed_PAIR_primary(self):
        sources, generic, controls, scores = fixture()
        scores['BASE_TRUE'] = copy.deepcopy(scores['PAIR_TRUE'])
        scores['PAIR_TRUE'] = copy.deepcopy(scores['OLD_PAIR_LOCAL'])
        result = compare_predictions(generic, controls, scores, sources)
        self.assertFalse(result['remaining_TRUE_pair_admitted'])
        self.assertFalse(result['checks']['primary_beats_old_PAIR_macro'])
        self.assertEqual(result['primary_role'], 'PAIR_TRUE')

    def test_mean_improvement_in_only_two_sources_is_rejected(self):
        sources, generic, controls, scores = fixture()
        for row in generic:
            if row['source_id'] in sources[2:]:
                for case in (row['first_id'], row['reverse_id']): scores['PAIR_TRUE'][case] = scores['OLD_PAIR_LOCAL'][case]
        result = compare_predictions(generic, controls, scores, sources)
        self.assertTrue(result['checks']['primary_beats_old_PAIR_macro'])
        self.assertFalse(result['checks']['at_least3_sources_beat_old_PAIR'])
        self.assertFalse(result['remaining_TRUE_pair_admitted'])

    def test_same_foreign_scores_and_one_failed_self_control_each_stop(self):
        sources, generic, controls, scores = fixture()
        scores['PAIR_FOREIGN'] = {case: value for case, value in scores['PAIR_TRUE'].items() if 'SELF' not in case}
        result = compare_predictions(generic, controls, scores, sources)
        self.assertFalse(result['checks']['primary_beats_foreign_macro'])
        self.assertFalse(result['remaining_TRUE_pair_admitted'])
        sources, generic, controls, scores = fixture()
        scores['PAIR_TRUE'][controls[0]['first_id']] = [.7, .1, .2]
        result = compare_predictions(generic, controls, scores, sources)
        self.assertFalse(result['checks']['all5_self_controls_strict_TIE'])
        self.assertFalse(result['remaining_TRUE_pair_admitted'])

    def test_swap_scores_are_scored_before_averaging(self):
        sources, generic, controls, scores = fixture()
        row = generic[0]
        scores['PAIR_TRUE'][row['first_id']] = [1., 0., 0.]
        scores['PAIR_TRUE'][row['reverse_id']] = [0., .4, .6]
        result = compare_predictions(generic, controls, scores, sources)
        expected = (sum((np.array([1., 0., 0.])-row['target'])**2)+
                    sum((np.array([.4, 0., .6])-row['target'])**2))/2/4
        self.assertAlmostEqual(result['metrics']['PAIR_TRUE']['generic']['per_source'][sources[0]]['distribution_brier'], expected)
        self.assertGreater(result['metrics']['PAIR_TRUE']['generic']['macro']['swap_total_variation'], 0.)

    def test_pilot_join_excludes_policy_and_rejects_partial_order(self):
        sources, generic, controls, _ = fixture()
        true = {r[k] for r in generic+controls for k in ('first_id', 'reverse_id')}
        foreign = {r[k] for r in generic for k in ('first_id', 'reverse_id')}
        extra = dict(generic[0], purpose='FIXED_ADDITION_POLICY')
        a, b = select_pilot_targets(dict(pairs=generic+controls+[extra]), true, foreign, sources)
        self.assertEqual((len(a), len(b)), (20, 5))
        with self.assertRaises(ValueError):
            select_pilot_targets(dict(pairs=generic+controls), true-{generic[0]['first_id']}, foreign, sources)

    def test_prefix_length_and_timestamp_difference_is_reported_not_hidden(self):
        row = dict(source_id='S0', prefix_tokens=100, video_grid_thw=[[32, 16, 16], [4, 16, 16], [4, 16, 16]],
                   overview_timestamps=['0', '2'], input=dict(path='true'))
        other = dict(row, prefix_tokens=103, overview_timestamps=['0', '9'], input=dict(path='foreign'))
        result = prefix_differences({'X': row}, {'X': other})
        self.assertEqual(result[0]['true_minus_foreign_prefix_tokens'], -3)
        self.assertFalse(result[0]['overview_timestamps_equal'])
        other['video_grid_thw'] = [[31, 16, 16], [4, 16, 16], [4, 16, 16]]
        with self.assertRaises(ValueError): prefix_differences({'X': row}, {'X': other})


class RawTests(unittest.TestCase):
    def receipt(self, raw):
        ids = [1, 3, 5]; logits = raw[ids].double(); p = torch.softmax(logits, dim=0)
        return dict(full_vocabulary_size=len(raw), class_token_ids=ids, raw_dtype='torch.float32',
                    class_logits=logits.tolist(), probabilities=p.tolist(), predicted_index=int(torch.argmax(p)))

    def test_full_vocabulary_and_independent_float64_class_probabilities(self):
        raw = torch.tensor([123., 1., -234., 2., 99., -4.], dtype=torch.float32)
        receipt = self.receipt(raw)
        p = validate_raw(raw, receipt, [1, 3, 5], 6)
        np.testing.assert_array_equal(p, receipt['probabilities'])
        # Large unrelated vocabulary values do not normalize the three-class score.
        self.assertGreater(p[1], .7)

    def test_truncation_nonfinite_wrong_class_and_processed_score_rejected(self):
        raw = torch.arange(6, dtype=torch.float32); receipt = self.receipt(raw)
        with self.assertRaises(ValueError): validate_raw(raw[:5], receipt, [1, 3, 5], 6)
        bad = raw.clone(); bad[0] = float('nan')
        with self.assertRaises(ValueError): validate_raw(bad, receipt, [1, 3, 5], 6)
        with self.assertRaises(ValueError): validate_raw(raw.half(), receipt, [1, 3, 5], 6)
        with self.assertRaises(ValueError): validate_raw(raw, receipt, [0, 3, 5], 6)
        receipt['probabilities'] = [.1, .2, .7]
        with self.assertRaises(ValueError): validate_raw(raw, receipt, [1, 3, 5], 6)

    def test_alias_requires_same_role_input_classes_and_all_source_owners(self):
        original = dict(model_role='PAIR_TRUE', source_id='S0', source_sha256='a'*64,
            overview_source_id='S0', overview_source_sha256='a'*64, overview_is_foreign=False,
            input_signature=dict(synthetic='same'), class_token_ids=[1, 3, 5], raw_logits=dict(path='raw', sha256='r'),
            actual_new_forward=True, alias_of=None)
        first = dict(path='first', sha256='f'); second = dict(path='second', sha256='s')
        key = validate_alias(original, first, {}, set())
        prior = {'first': dict(reference=first, receipt=original)}
        alias = dict(original, actual_new_forward=False, alias_of=first)
        self.assertEqual(validate_alias(alias, second, prior, {key}), key)
        for changed in (dict(model_role='PAIR_FOREIGN'), dict(source_id='S1'),
                        dict(overview_source_id='S2', overview_source_sha256='b'*64, overview_is_foreign=True),
                        dict(class_token_ids=[0, 3, 5]), dict(input_signature=dict(synthetic='changed'))):
            with self.assertRaises(ValueError): validate_alias(dict(alias, **changed), second, prior, {key})
        with self.assertRaises(ValueError): validate_alias(original, second, prior, {key})
        with self.assertRaises(ValueError): validate_alias(alias, second, {}, {key})


if __name__ == '__main__':
    unittest.main()
