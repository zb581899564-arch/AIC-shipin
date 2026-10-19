import json
from pathlib import Path
import tempfile
import unittest

import numpy as np

from relative_time_rank import (PCA_DIM, RIDGE_LAMBDA, apply_selection, fit,
                                predict, select_window, source_center)


class RelativeRankTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        rng = np.random.default_rng(42)
        cls.sources = {}
        for i in range(3):
            x = rng.integers(-8, 9, size=(15+i, 40)).astype(np.float32)
            n = rng.integers(1, 8, size=len(x))
            cls.sources[str(i)] = dict(features=x, native_counts=n,
                                      softvote=.4 + .02*x[:, 0].astype(np.float64)
                                      - .01*x[:, 1].astype(np.float64))
        cls.ids = list(cls.sources)
        cls.state, cls.report = fit(cls.sources, cls.ids, synthetic=True)

    def test_source_offsets_do_not_change_queries_or_centered_targets(self):
        row = self.sources['0']
        before = predict(self.state, row['features'], row['native_counts'])
        after = predict(self.state, row['features']+np.float32(32), row['native_counts'])
        np.testing.assert_array_equal(before, after)
        a, _, _ = source_center(row['softvote'], row['native_counts'])
        b, _, _ = source_center(row['softvote']+.1, row['native_counts'])
        np.testing.assert_allclose(a, b, atol=2e-16)

    def test_train_source_offsets_invariant_and_no_eval_access(self):
        shifted = {sid: dict(features=r['features']+np.float32(16*(i+1)),
                             native_counts=r['native_counts'], softvote=r['softvote']+.01*(i+1))
                   for i, (sid, r) in enumerate(self.sources.items())}
        shifted['never_access_eval'] = {'features': 'invalid eval sentinel'}
        state, _ = fit(shifted, self.ids, synthetic=True)
        for sid in self.ids:
            r = self.sources[sid]
            np.testing.assert_allclose(predict(self.state, r['features'], r['native_counts']),
                                       predict(state, shifted[sid]['features'], r['native_counts']), atol=2e-7)

    def test_native_weight_center_and_pairwise_identity(self):
        x = np.array([[1., 3.], [4., 2.], [-2., 5.]])
        y = np.array([.1, .8, .3]); n = np.array([1, 2, 7])
        xc, mean, w = source_center(x, n)
        yc, _, _ = source_center(y, n)
        np.testing.assert_allclose(w, [.1, .2, .7])
        np.testing.assert_allclose(mean, np.average(x, weights=n, axis=0))
        np.testing.assert_allclose(w @ xc, [0., 0.], atol=1e-15)
        beta = np.array([.2, -.4]); residual = xc @ beta-yc
        centered_loss = np.sum(w*residual**2)
        pair_loss = .5*sum(w[i]*w[j]*((x[i]-x[j]) @ beta-(y[i]-y[j]))**2
                           for i in range(3) for j in range(3))
        self.assertAlmostEqual(centered_loss, pair_loss, places=14)

    def test_source_equal_ridge_normal_equations_and_no_intercept(self):
        design, target, weights = [], [], []
        for sid in self.ids:
            r = self.sources[sid]
            xc, _, w = source_center(r['features'], r['native_counts'])
            yc, _, _ = source_center(r['softvote'], r['native_counts'])
            design.append(((xc/self.state['RMS']).astype(np.float32) @ self.state['PCA']).astype(np.float64))
            target.append(yc); weights.append(w/len(self.ids))
        x = np.concatenate(design); y = np.concatenate(target); w = np.concatenate(weights)
        b = self.state['beta']
        np.testing.assert_allclose(x.T @ (w*(x @ b-y))+RIDGE_LAMBDA*b, np.zeros(PCA_DIM), atol=1e-12)
        self.assertAlmostEqual(w.sum(), 1.)
        self.assertTrue(all(abs(v.sum()-1/3) < 1e-15 for v in weights))
        expected_rms = np.maximum(np.sqrt(sum(np.sum(ws[:, None]*source_center(self.sources[s]['features'],
                               self.sources[s]['native_counts'])[0]**2, axis=0)
                               for s, ws in zip(self.ids, weights))), 1e-4)
        np.testing.assert_array_equal(expected_rms, self.state['RMS'])
        self.assertEqual(set(self.state), {'RMS', 'PCA', 'beta'})
        self.assertFalse(self.report['intercept'])
        self.assertEqual(self.report['supervised_coefficients'], 32)

    def test_actual_npz_save_reload_queries_bit_equal(self):
        with tempfile.TemporaryDirectory() as d:
            path = Path(d)/'ranker.npz'
            np.savez(path, **self.state)
            with np.load(path, allow_pickle=False) as loaded:
                state = {k: loaded[k] for k in loaded.files}
            for r in self.sources.values():
                np.testing.assert_array_equal(predict(self.state, r['features'], r['native_counts']),
                                              predict(state, r['features'], r['native_counts']))

    def test_invalid_actual_recipe_and_native_weights_rejected(self):
        with self.assertRaises(ValueError): fit(self.sources, self.ids)
        with self.assertRaises(ValueError): predict(self.state, self.sources['0']['features'], np.zeros(15, int))
        with self.assertRaises(ValueError): source_center([1., np.nan], [1, 1])
        with self.assertRaises(ValueError): source_center([1., 2.], [1., 2.])


def ownership(group_count, *, odd_tail=False, cell_counts=None):
    cells = np.arange(2*group_count-int(odd_tail), dtype=np.int64)
    counts = np.ones(len(cells), dtype=np.int64) if cell_counts is None else np.asarray(cell_counts)
    old = np.repeat(cells, counts)
    return old//2, old


class FourGroupPolicyTests(unittest.TestCase):
    def test_ties_earliest_and_all_baseline_frames_retained(self):
        groups, old = ownership(12)
        baseline = groups < 4; original = baseline.copy()
        decision = select_window(np.r_[np.ones(4), np.full(8, 2.)], groups, old, baseline)
        self.assertEqual(decision['selected']['start_group'], 4)
        self.assertEqual(decision['baseline_anchor_count'], 1)
        self.assertEqual(decision['candidate_count'], 5)
        self.assertEqual(decision['intersecting_window_count'], 3)
        self.assertEqual(len(decision['windows']), 9)
        proposal = apply_selection(baseline, decision)
        self.assertTrue(proposal[baseline].all())
        self.assertEqual(proposal.sum()-baseline.sum(), 8)
        np.testing.assert_array_equal(original, baseline)
        json.dumps(decision, allow_nan=False)

    def test_strictly_equal_anchor_score_abstains(self):
        groups, old = ownership(8); baseline = groups < 4
        d = select_window(np.ones(8), groups, old, baseline)
        self.assertEqual(d['abstain_reason'], 'BEST_NOT_STRICTLY_ABOVE_ALL_BASELINE_ANCHORS')
        np.testing.assert_array_equal(apply_selection(baseline, d), baseline)

    def test_candidate_must_beat_every_baseline_anchor(self):
        groups, old = ownership(12); baseline = groups < 8
        d = select_window(np.r_[np.ones(4), np.full(4, 5.), np.full(4, 3.)], groups, old, baseline)
        self.assertEqual(d['baseline_anchor_count'], 5)
        self.assertEqual(d['baseline_max_score'], 5.)
        self.assertEqual(d['best_candidate_score'], 3.)
        self.assertEqual(d['abstain_reason'], 'BEST_NOT_STRICTLY_ABOVE_ALL_BASELINE_ANCHORS')

    def test_odd_final_group_is_not_a_complete_candidate(self):
        groups, old = ownership(8, odd_tail=True); baseline = groups < 4
        d = select_window(np.r_[np.zeros(4), np.full(4, 9.)], groups, old, baseline)
        self.assertEqual(d['incomplete_group_ids'], [7])
        self.assertEqual(d['candidate_count'], 0)
        self.assertEqual(d['incomplete_window_count'], 1)
        self.assertEqual(d['abstain_reason'], 'NO_DISJOINT_COMPLETE_CANDIDATE')

    def test_one_baseline_frame_intersection_rejects_whole_window(self):
        groups, old = ownership(8); baseline = groups < 4
        baseline[np.flatnonzero(groups == 6)[0]] = True
        d = select_window(np.r_[np.zeros(4), np.full(4, 9.)], groups, old, baseline)
        self.assertEqual(d['baseline_anchor_count'], 1)
        self.assertEqual(d['candidate_count'], 0)
        self.assertEqual(d['windows'][-1]['kind'], 'INTERSECTS_BASELINE')
        np.testing.assert_array_equal(apply_selection(baseline, d), baseline)

    def test_missing_baseline_anchor_is_never_vacuously_admitted(self):
        groups, old = ownership(8); baseline = np.zeros(len(groups), bool)
        d = select_window(np.arange(8, dtype=float), groups, old, baseline)
        self.assertEqual(d['candidate_count'], 5)
        self.assertEqual(d['abstain_reason'], 'NO_COMPLETE_BASELINE_ANCHOR')
        self.assertIsNone(d['selected'])

    def test_all_retained_or_short_source_abstains(self):
        for count in (3, 8):
            groups, old = ownership(count); baseline = np.ones(len(groups), bool)
            d = select_window(np.arange(count, dtype=float), groups, old, baseline)
            self.assertIsNone(d['selected'])
            np.testing.assert_array_equal(apply_selection(baseline, d), baseline)

    def test_window_scores_use_native_counts(self):
        groups, old = ownership(8, cell_counts=[1]*8+[1, 1, 1, 1, 1, 1, 7, 7])
        baseline = groups < 4; scores = np.r_[np.zeros(4), [0., 0., 0., 8.]]
        d = select_window(scores, groups, old, baseline)
        expected = np.average(scores[4:], weights=np.bincount(groups)[4:])
        self.assertAlmostEqual(d['selected']['score'], expected)
        self.assertNotEqual(d['selected']['score'], scores[4:].mean())

    def test_wrong_native_mapping_and_nonbool_baseline_rejected(self):
        groups, old = ownership(8); baseline = groups < 4
        with self.assertRaises(ValueError): select_window(np.zeros(8), groups+1, old, baseline)
        with self.assertRaises(ValueError): select_window(np.zeros(8), groups, old, baseline.astype(int))
        bad = old.copy(); bad[-1] += 1
        with self.assertRaises(ValueError): select_window(np.zeros(8), groups, bad, baseline)


if __name__ == '__main__':
    unittest.main()
