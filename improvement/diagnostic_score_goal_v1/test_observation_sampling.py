"""Synthetic clocks and Boolean references only; no real data or model calls."""
import copy
from fractions import Fraction
import json
import unittest

import numpy as np

from observation_sampling import (APPLICABLE, INAPPLICABLE, compare_observations,
                                  sample_uniform_native, augment_native_samples)


def cfr(count=64):
    return [str(Fraction(i, 16)) for i in range(count)]


def sample():
    return sample_uniform_native(cfr(), 0, 64, source_end_exact='4')


OLD = list(range(0, 64, 8))


class ObservationTests(unittest.TestCase):
    def test_nested_old8_plus24_exact_farthest_point_and_explicit_inapplicability(self):
        result = augment_native_samples(cfr(), 0, 64, OLD, source_end_exact=4)
        self.assertEqual(result['status'], APPLICABLE)
        self.assertTrue(set(OLD) <= set(result['sample_ordinals']))
        self.assertEqual(len(result['sample_ordinals']), 32)
        self.assertEqual(len(result['added_sample_ordinals']), 24)
        self.assertEqual(result['augmentation_step_ordinals'][:3], [63, 4, 12])
        self.assertEqual(result['augmentation_step_min_distance_exact'][:3], ['7/16', '1/4', '1/4'])
        self.assertEqual(result, augment_native_samples(cfr(), 0, 64, OLD, source_end_exact=4))
        # Independent brute-force definition confirms all24 steps and tie order.
        points = list(map(Fraction, cfr())); selected = set(OLD)
        for chosen in result['augmentation_step_ordinals']:
            ranked = sorted((min(abs(points[i]-points[j]) for j in selected), -i, i)
                            for i in range(64) if i not in selected)
            self.assertEqual(chosen, ranked[-1][2]); selected.add(chosen)
        labels = np.zeros((64, 2), bool); labels[0:4, 0] = True; labels[10:13, 1] = True
        comparison = compare_observations(labels, OLD, result)
        self.assertTrue(comparison['nested_original8_preserved'])
        a = comparison['views']['OLD8']['positive_component_observability']
        b = comparison['views']['NEW32']['positive_component_observability']
        self.assertGreaterEqual(b['observed_positive_components'], a['observed_positive_components'])
        self.assertGreaterEqual(b['hit_component_native_frames'], a['hit_component_native_frames'])
        short = augment_native_samples(cfr(), 0, 31, list(range(0, 31, 4)), source_end_exact=4)
        self.assertEqual(short['status'], INAPPLICABLE); self.assertIsNone(short['sample_ordinals'])
        self.assertEqual(short['original_sample_ordinals'], list(range(0, 31, 4)))
        with self.assertRaises(ValueError): augment_native_samples(cfr(), 0, 64, [0]*8, source_end_exact=4)

    def test_fixed32_uniform_targets_exact_and_end_exclusive(self):
        result = sample()
        self.assertEqual(result['status'], APPLICABLE)
        self.assertEqual(result['sample_ordinals'], list(range(0, 64, 2)))
        self.assertEqual(result['target_exact_pts'], [str(Fraction(i, 8)) for i in range(32)])
        self.assertEqual(result['native_range_half_open'], [0, 64])
        self.assertNotIn('4', result['sample_exact_pts'])
        self.assertFalse(result['selection_uses_labels'])

    def test_native_subclip_bounds_use_pts_hi_not_physical_end(self):
        result = sample_uniform_native(cfr(96), 16, 80, source_end_exact='6')
        self.assertEqual(result['clip_start_exact'], '1')
        self.assertEqual(result['clip_end_exact'], '5')
        self.assertEqual(result['sample_ordinals'], list(range(16, 80, 2)))
        self.assertEqual(result['native_range_half_open'], [16, 80])

    def test_vfr_exact_nearest_ties_choose_earlier_native_ordinal(self):
        points = [0]+[2*i+1 for i in range(1, 64)]
        result = sample_uniform_native(points, 0, 64, source_end_exact=128)
        self.assertEqual(result['status'], APPLICABLE)
        self.assertEqual(result['sample_ordinals'], [0]+[2*i-1 for i in range(1, 32)])
        self.assertEqual(result['target_exact_pts'][1], '4')
        self.assertEqual(result['sample_exact_pts'][1], '3')

    def test_insufficient_native_frames_is_explicit_not_padded_or_empty_success(self):
        result = sample_uniform_native(cfr(), 0, 31, source_end_exact=4)
        self.assertEqual(result['status'], INAPPLICABLE)
        self.assertEqual(result['eligible_native_frames'], 31)
        self.assertIsNone(result['sample_ordinals'])
        self.assertIsNone(result['attempted_nearest_ordinals'])
        self.assertEqual(result['reason'], 'FEWER_THAN32_NATIVE_FRAMES_IN_REGISTERED_CLIP')

    def test_vfr_duplicate_nearest_choices_are_not_repaired(self):
        points = [str(Fraction(i, 1000)) for i in range(31)]+['99']
        result = sample_uniform_native(points, 0, 32, source_end_exact=100)
        self.assertEqual(result['status'], INAPPLICABLE)
        self.assertEqual(result['eligible_native_frames'], 32)
        self.assertLess(result['distinct_nearest_native_frames'], 32)
        self.assertEqual(len(result['attempted_nearest_ordinals']), 32)
        self.assertIsNone(result['sample_ordinals'])
        self.assertFalse(result['padding_or_duplicate_repair'])

    def test_invalid_clocks_bounds_or_sample_count_fail(self):
        cases = [(cfr(), -1, 64, 4, 32), (cfr(), 0, 65, 4, 32), (cfr(), 8, 8, 4, 32),
                 (cfr(), True, 64, 4, 32), (cfr(), 0, 64, '63/16', 32),
                 (cfr(), 0, 64, 4., 32), (cfr(), 0, 64, 4, 8),
                 (['0', '0', '1'], 0, 3, 2, 32), ([0., 1.], 0, 2, 2, 32)]
        for points, lo, hi, end, count in cases:
            with self.subTest(case=(lo, hi, end, count)), self.assertRaises(ValueError):
                sample_uniform_native(points, lo, hi, source_end_exact=end, samples=count)

    def test_all_rater_densities_positive_components_and_original_gt_unchanged(self):
        labels = np.zeros((64, 3), dtype=np.bool_)
        labels[2:4, 0] = True; labels[10:12, 1] = True; labels[31, 1] = True
        saved = labels.copy(); plan = sample(); saved_plan = copy.deepcopy(plan)
        result = compare_observations(labels, OLD, plan)
        np.testing.assert_array_equal(labels, saved); self.assertEqual(plan, saved_plan)
        self.assertEqual(result['original_raters'], 3)
        self.assertEqual(result['full_native_density_per_rater'], [2/64, 3/64, 0.])
        old, new, full = [result['views'][key] for key in ('OLD8', 'NEW32', 'FULL_NATIVE')]
        self.assertEqual(old['density_per_rater'], [0., 0., 0.])
        self.assertEqual(new['density_per_rater'], [1/32, 1/32, 0.])
        self.assertAlmostEqual(new['mean_absolute_density_error'], 1/192)
        self.assertEqual(old['positive_component_observability']['missed_positive_components'], 3)
        self.assertEqual(new['positive_component_observability']['observed_positive_components'], 2)
        self.assertEqual(new['positive_component_observability']['missed_positive_components'], 1)
        self.assertEqual(full['positive_component_observability']['missed_positive_components'], 0)
        self.assertEqual(full['mean_absolute_density_error'], 0.)
        self.assertIsNone(old['positive_component_observability']['per_rater'][2]['component_observation_fraction'])
        self.assertFalse(result['model_quality_established'])
        json.dumps(result, allow_nan=False)

    def test_nearest_observation_native_reconstruction_ties_earlier(self):
        labels = np.zeros((64, 1), dtype=np.bool_); labels[0, 0] = True
        result = compare_observations(labels, OLD, sample())
        old = result['views']['OLD8']['nearest_observation_native_reconstruction']
        new = result['views']['NEW32']['nearest_observation_native_reconstruction']
        # Native frame4 ties observations0/8, and belongs to earlier observation0.
        self.assertEqual(old['observation_native_frame_weights'][0], 5)
        self.assertEqual(sum(old['observation_native_frame_weights']), 64)
        self.assertEqual(old['density_per_rater'], [5/64])
        self.assertEqual(old['native_reference_disagreement_fraction_per_rater'], [4/64])
        self.assertEqual(new['density_per_rater'], [2/64])
        self.assertEqual(new['native_reference_disagreement_fraction_per_rater'], [1/64])
        self.assertFalse(old['new_dense_GT_created']); self.assertFalse(old['usable_as_training_labels'])

    def test_inapplicable_new32_keeps_old8_full_and_no_positive_is_not_perfect_coverage(self):
        plan = sample_uniform_native(cfr(), 0, 31, source_end_exact=4)
        result = compare_observations(np.zeros((64, 2), bool), list(range(0, 31, 4)), plan)
        self.assertFalse(result['new32_applicable']); self.assertIsNone(result['views']['NEW32'])
        self.assertEqual(result['views']['OLD8']['samples'], 8)
        self.assertEqual(result['views']['FULL_NATIVE']['samples'], 31)
        self.assertIsNone(result['views']['OLD8']['positive_component_observability']['macro_component_observation_fraction'])

    def test_invalid_old_observations_labels_and_forged_new_state_fail(self):
        labels = np.zeros((64, 2), bool)
        for old in (OLD[:-1], [0]*8, [0, 8, 16, 24, 32, 40, 48, 64], [float(i) for i in OLD]):
            with self.assertRaises(ValueError): compare_observations(labels, old, sample())
        for bad in (labels.astype(float), labels[:-1], np.empty((64, 0), bool)):
            with self.assertRaises(ValueError): compare_observations(bad, OLD, sample())
        forged = sample(); forged['sample_ordinals'][1] = 0
        with self.assertRaises(ValueError): compare_observations(labels, OLD, forged)

    def test_nonzero_clip_component_boundaries_and_labels_cannot_change_samples(self):
        plan = sample_uniform_native(cfr(96), 16, 80, source_end_exact=6)
        before = copy.deepcopy(plan); labels = np.zeros((96, 1), bool)
        labels[14:19] = True; labels[78:83] = True
        result = compare_observations(labels, list(range(16, 80, 8)), plan)
        spans = result['views']['OLD8']['positive_component_observability']['per_rater'][0]
        self.assertEqual(spans['reference_components_native_half_open'], [[16, 19], [78, 80]])
        self.assertEqual(spans['component_hits'], [True, False])
        compare_observations(~labels, list(range(16, 80, 8)), plan)
        self.assertEqual(plan, before)
        self.assertEqual(sample_uniform_native(cfr(96), 16, 80, source_end_exact=6), before)


if __name__ == '__main__':
    unittest.main()
