import io
import json
import unittest

import numpy as np

from marginal_utility_head import build_design, fit_heads, predict, select_addition


def clip(first, last, groups=None):
    row = dict(native_start=first, native_end_exclusive=last, native_frames=last-first)
    if groups is not None:
        row.update(start_group=groups, end_group_exclusive=groups+4)
    return row


def feature_fixture(values, counts=None):
    n = len(values)
    features = np.zeros((n, 8192), np.float32)
    features[:, 0] = values
    groups = np.repeat(np.arange(n), np.ones(n, int) if counts is None else counts)
    projection = np.zeros((8192, 16), np.float32); projection[:16] = np.eye(16, dtype=np.float32)
    return features, groups, dict(RMS=np.ones(8192, np.float64), PCA16=projection)


def train_fixture():
    ids = ['S%02d' % i for i in range(20)]
    designs, targets = {}, {}
    for i, sid in enumerate(ids):
        x = np.zeros((2+i % 3, 19), np.float64)
        x[:, 0] = np.linspace(-1, 1, len(x))
        x[:, 16] = x[:, 0]**2
        x[:, 17] = .1+.02*i
        x[:, 18] = np.linspace(.01, .04, len(x))
        designs[sid] = x
        targets[sid] = 2+.1*i+.4*x[:, 0]
    return ids, designs, targets


class DesignTests(unittest.TestCase):
    def test_native_weighted_source_and_partial_baseline_pooling(self):
        features, groups, transform = feature_fixture(np.arange(8), [1, 3, 1, 1, 1, 1, 1, 1])
        baseline = np.zeros(len(groups), bool)
        baseline[0] = True; baseline[1] = True  # Only one of the three native frames owned by group1.
        lo = int((groups < 4).sum())
        design = build_design(features, groups, baseline, [clip(lo, len(groups), 4)], transform)
        # Source centering cancels in C-B; C mean5.5 minus selected B mean0.5.
        self.assertEqual(design.shape, (1, 19))
        self.assertAlmostEqual(design[0, 0], 5.)
        self.assertAlmostEqual(design[0, 16], 25/16)
        self.assertAlmostEqual(design[0, 17], 2/10)
        self.assertAlmostEqual(design[0, 18], 4/10)

    def test_baseline_state_can_reverse_within_source_candidate_distance_order(self):
        features, groups, transform = feature_fixture([0]*4+[2]*4+[10]*4+[12]*4)
        candidates = [clip(0, 4, 0), clip(12, 16, 12)]
        left = np.zeros(16, bool); left[4:8] = True
        right = np.zeros(16, bool); right[8:12] = True
        a = build_design(features, groups, left, candidates, transform)
        b = build_design(features, groups, right, candidates, transform)
        self.assertLess(a[0, 16], a[1, 16])
        self.assertGreater(b[0, 16], b[1, 16])
        # A model using -distance reverses its within-source ranking when B changes.
        self.assertEqual(np.argmax(-a[:, 16]), 0)
        self.assertEqual(np.argmax(-b[:, 16]), 1)
        self.assertEqual(a[:, 17:].tolist(), b[:, 17:].tolist())

    def test_empty_baseline_zero_pc_pool_and_empty_candidates(self):
        features, groups, transform = feature_fixture(np.arange(8))
        baseline = np.zeros(8, bool)
        result = build_design(features, groups, baseline, [clip(0, 4, 0)], transform)
        self.assertAlmostEqual(result[0, 0], -2.)
        self.assertEqual(result[0, 17], 0.)
        self.assertEqual(build_design(features, groups, baseline, [], transform).shape, (0, 19))

    def test_unknowns_overlap_incomplete_group_and_transform_rejected(self):
        features, groups, transform = feature_fixture(np.arange(8))
        baseline = np.zeros(8, bool); baseline[0] = True
        for bad in (baseline.astype(float), np.array([None]*8, object), baseline[:-1]):
            with self.assertRaises(ValueError): build_design(features, groups, bad, [], transform)
        with self.assertRaises(ValueError): build_design(features, groups, baseline, [clip(0, 4, 0)], transform)
        with self.assertRaises(ValueError): build_design(features, groups, baseline, [clip(4, 7)], transform)
        with self.assertRaises(ValueError): build_design(features, groups, baseline, [clip(3, 7)], transform)
        with self.assertRaises(ValueError): build_design(features.astype(float), groups, baseline, [], transform)
        with self.assertRaises(ValueError): build_design(features, groups, baseline, [], dict(transform, beta=np.zeros(16)))


class FitTests(unittest.TestCase):
    def test_global_intercept_preserves_source_target_level_and_same_source_weights(self):
        ids, designs, targets = train_fixture()
        state, report = fit_heads(designs, targets, ids)
        expected = np.mean([np.mean(targets[sid]) for sid in ids])
        self.assertAlmostEqual(float(state['constant_z']), expected)
        self.assertGreater(float(state['visual_intercept']), 2.)
        self.assertFalse(report['source_centered_targets'])
        self.assertEqual(report['closed_form_solves'], 2)
        self.assertEqual(report['new_PCA_fits'], 0)
        self.assertEqual(report['lambda_value'], .01)
        for row in report['source_rows']:
            self.assertAlmostEqual(row['candidate_weight']*row['candidates'], 1/20)
        # Both heads use exactly the same source-equal means and scales for metadata.
        np.testing.assert_array_equal(state['visual_mean'][17:], state['metadata_mean'])
        np.testing.assert_array_equal(state['visual_scale'][17:], state['metadata_scale'])
        self.assertEqual(float(state['visual_intercept']), float(state['metadata_intercept']))
        json.dumps(report, allow_nan=False)

    def test_duplicate_all_candidates_in_one_source_does_not_change_source_weight(self):
        ids, designs, targets = train_fixture()
        first, _ = fit_heads(designs, targets, ids)
        designs[ids[0]] = np.repeat(designs[ids[0]], 3, axis=0)
        targets[ids[0]] = np.repeat(targets[ids[0]], 3)
        second, _ = fit_heads(designs, targets, ids)
        for key in first: np.testing.assert_allclose(first[key], second[key], atol=2e-12, rtol=2e-12)

    def test_metadata_control_cannot_use_visual_columns(self):
        ids, designs, targets = train_fixture()
        state, _ = fit_heads(designs, targets, ids)
        original = designs[ids[0]].copy(); changed = original.copy(); changed[:, :17] += 100
        a, b = predict(state, original), predict(state, changed)
        np.testing.assert_array_equal(a['METADATA'], b['METADATA'])
        np.testing.assert_array_equal(a['CONSTANT'], b['CONSTANT'])
        self.assertFalse(np.array_equal(a['VISUAL'], b['VISUAL']))

    def test_flat_numpy_save_reload_and_label_free_query_are_bit_exact(self):
        ids, designs, targets = train_fixture()
        designs['UNREAD_DEV'] = object(); targets['UNREAD_DEV'] = object()
        state, _ = fit_heads(designs, targets, ids)
        stream = io.BytesIO(); np.savez(stream, **state); stream.seek(0)
        with np.load(stream, allow_pickle=False) as saved: restored = {key: saved[key].copy() for key in saved.files}
        a, b = predict(state, designs[ids[1]]), predict(restored, designs[ids[1]])
        for role in a: np.testing.assert_array_equal(a[role], b[role])
        for role, values in predict(restored, np.empty((0, 19), np.float64)).items(): self.assertEqual(values.shape, (0,))

    def test_invalid_train_sources_targets_and_old_state_rejected(self):
        ids, designs, targets = train_fixture()
        with self.assertRaises(ValueError): fit_heads(designs, targets, ids[:-1])
        targets[ids[0]] = np.array([np.nan, 1.])
        with self.assertRaises(ValueError): fit_heads(designs, targets, ids)
        with self.assertRaises(ValueError): predict(dict(RMS=np.ones(8192), PCA=np.zeros((8192, 32)), beta=np.ones(32)), designs[ids[1]])


class PolicyTests(unittest.TestCase):
    def test_rank_actual_delta_instead_of_normalized_z(self):
        result = select_addition([clip(0, 2), clip(4, 12)], np.array([2., 1.]), 20)
        self.assertEqual(result['selected']['native_start'], 4)
        self.assertAlmostEqual(result['predicted_delta'], .8)
        self.assertEqual(result['baseline_frames_removed'], 0)

    def test_strict_positive_ties_earliest_and_abstain(self):
        clips = [clip(4, 8), clip(0, 4)]
        result = select_addition(clips, np.array([1., 1.]), 12)
        self.assertEqual(result['selected']['native_start'], 0)
        self.assertEqual(result['added_native_frames'], 4)
        for values in ([0., 0.], [-1., 0.], [-1., -2.]):
            result = select_addition(clips, np.array(values), 12)
            self.assertIsNone(result['selected']); self.assertEqual(result['predicted_delta'], 0.)
        self.assertEqual(select_addition([], np.array([], float), 12)['abstain_reason'], 'NO_CANDIDATES')

    def test_invalid_policy_mapping_is_not_an_empty_success(self):
        for clips, scores, n in (([clip(0, 4)], [np.nan], 8), ([clip(0, 4)], [], 8),
                                 ([clip(0, 4), clip(2, 6)], [1., 2.], 8), ([clip(0, 4)], [1.], 0)):
            with self.assertRaises(ValueError): select_addition(clips, np.asarray(scores), n)


if __name__ == '__main__':
    unittest.main()
