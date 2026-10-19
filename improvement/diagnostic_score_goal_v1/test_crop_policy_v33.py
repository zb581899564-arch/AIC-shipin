"""Synthetic v33 math only; JSON roundtrip is in memory, no data/model/file IO."""
import json
import unittest

import numpy as np

import crop_policy_v33 as policy


POOL = [[0, 0, 16], [8, 0, 16], [0, 0, 8]]


def pair(index, forward=.7, reverse=.7):
    return dict(candidate_index=index, forward_probs=[(1-forward)/2, forward, (1-forward)/2],
                reverse_probs=[reverse, (1-reverse)/2, (1-reverse)/2])


def metric_rows(count, gain=.02):
    return [dict(source_id=str(i), baseline_iou=.5, selected_iou=.5+gain, geometry_iou=.51,
                 oracle_iou=.9, selected_index=1, baseline_index=0) for i in range(count)]


class CropPolicyTests(unittest.TestCase):
    def test_dualswap_both_strict_majorities_and_earlier_exact_tie(self):
        self.assertEqual(policy.select_pool(POOL, 0, [pair(2, .8, .6), pair(1, .6, .8)]), 1)
        self.assertEqual(policy.select_pool(POOL, 0, [pair(1, .99, .49), pair(2, .5, .99)]), 0)
        self.assertEqual(policy.select_pool(POOL, 0, [pair(1, .51, .52), pair(2, .7, .7)]), 2)
        self.assertEqual(policy.select_pool([POOL[0]], 0, []), 0)
        self.assertTrue(policy.strict_tie([.1, .2, .7]))
        self.assertFalse(policy.strict_tie([.2, .4, .4]))

    def test_probability_unknown_missing_duplicate_and_invalid_inputs_fail(self):
        for bad in ([.1, .2], [.1, .2, .8], [-.1, .2, .9], [float('nan'), .2, .8], [None, .2, .8]):
            with self.assertRaises(ValueError): policy.strict_tie(bad)
        with self.assertRaises(ValueError): policy.select_pool(POOL, 0, [pair(1)])
        with self.assertRaises(ValueError): policy.select_pool(POOL, 0, [pair(1), pair(1)])
        with self.assertRaises(ValueError): policy.select_pool(POOL, 0, [pair(1), pair(3)])
        with self.assertRaises(ValueError): policy.select_pool(POOL, 0, [pair(0), pair(2)])

    def test_thirteen_exact_features_and_native_legality(self):
        values = policy.geometry_features([8, 4, 16], 32, 18)
        x, y, w, h = .25, 4/18, .5, .5
        expected = [1, x, y, w, h, x*x, y*y, w*w, h*h, x*y, x*w, y*h, np.log(32/18)]
        np.testing.assert_array_equal(values, np.array(expected, dtype=np.float64))
        self.assertEqual(values.dtype, np.float64)
        with self.assertRaises(ValueError): policy.geometry_features([8, 10, 16], 32, 18)

    def test_fit_source_equal_weights_matches_closed_form_not_candidate_equal(self):
        sources = [dict(source_id='a', width=32, height=18, pool=[POOL[0]], candidate_ious=[.1]),
            dict(source_id='b', width=32, height=18, pool=POOL, candidate_ious=[.8, .7, .6])]
        x = np.stack([policy.geometry_features(b, 32, 18) for s in sources for b in s['pool']])
        y = np.array([.1, .8, .7, .6]); weights = np.array([.5, 1/6, 1/6, 1/6])
        penalty = np.diag([0]+[.01]*12)
        expected = np.linalg.solve(x.T@(weights[:, None]*x)+penalty, x.T@(weights*y))
        actual = policy.fit_geometry(sources)
        np.testing.assert_allclose(actual, expected, rtol=1e-12, atol=1e-12)
        candidate_equal = np.linalg.solve(x.T@x/4+penalty, x.T@y/4)
        self.assertGreater(float(np.max(abs(actual-candidate_equal))), .01)

    def test_intercept_unpenalized_and_json_reload_same_selection(self):
        sources = [dict(source_id='a', width=32, height=18, pool=POOL, candidate_ious=[.4]*3)]
        beta = policy.fit_geometry(sources)
        self.assertAlmostEqual(beta[0], .4, places=12)
        np.testing.assert_allclose(beta[1:], 0., atol=1e-12)
        reloaded = np.array(json.loads(json.dumps(beta.tolist())), dtype=np.float64)
        np.testing.assert_array_equal(beta, reloaded)
        self.assertEqual(policy.geometry_select(POOL, 32, 18, beta), policy.geometry_select(POOL, 32, 18, reloaded))
        self.assertEqual(policy.geometry_select(POOL, 32, 18, np.zeros(13), baseline_index=2), 2)

    def test_fit_unknown_targets_duplicate_sources_nonfinite_coefficients_fail(self):
        source = dict(source_id='a', width=32, height=18, pool=POOL, candidate_ious=[.1, None, .2])
        with self.assertRaises(ValueError): policy.fit_geometry([source])
        source['candidate_ious'] = [.1, .2, .3]
        with self.assertRaises(ValueError): policy.fit_geometry([source, source])
        with self.assertRaises(ValueError): policy.geometry_select(POOL, 32, 18, [float('nan')]*13)
        with self.assertRaises(ValueError): policy.fit_geometry([])

    def test_macro_metrics_oracle_diagnostic_and_worst_loss(self):
        rows = metric_rows(3)
        rows[1].update(selected_iou=.4, selected_index=0)
        rows[2].update(selected_iou=.5, selected_index=2)
        summary = policy.summarize(rows)
        self.assertEqual((summary['improved'], summary['degraded'], summary['unchanged_iou']), (1, 1, 1))
        self.assertEqual(summary['changed'], 2)
        self.assertAlmostEqual(summary['worst_loss'], .1)
        self.assertAlmostEqual(summary['mean_gain'], (.02-.1)/3)
        self.assertTrue(summary['oracle_is_reference_assisted_diagnostic'])
        with self.assertRaises(ValueError): policy.summarize([rows[0], rows[0]])
        rows[0]['selected_iou'] = None
        with self.assertRaises(ValueError): policy.summarize(rows)

    def test_frozen_screen_and_confirm_gates_plus_zeroactions_rejected(self):
        for phase, count in (('screen20', 20), ('confirm19', 19)):
            summary = policy.summarize(metric_rows(count))
            self.assertTrue(policy.quality_checks(summary, phase, count, 0)['admitted'])
            self.assertFalse(policy.quality_checks(summary, phase, count-1, 0)['admitted'])
            self.assertFalse(policy.quality_checks(summary, phase, count, 1)['admitted'])
            bad = dict(summary, changed=0)
            self.assertFalse(policy.quality_checks(bad, phase, count, 0)['admitted'])
            bad = dict(summary, mean_gain_vs_geometry=0.)
            self.assertFalse(policy.quality_checks(bad, phase, count, 0)['admitted'])
        summary = policy.summarize(metric_rows(20))
        for field, value in (('mean_gain', .0099), ('improved', 4), ('worst_loss', .10001)):
            self.assertFalse(policy.quality_checks(dict(summary, **{field:value}), 'screen20', 20, 0)['admitted'])
        self.assertFalse(policy.quality_checks(policy.summarize(metric_rows(19)), 'screen20', 19, 0)['admitted'])
        with self.assertRaises(ValueError): policy.quality_checks(summary, 'unknown', 20, 0)
        with self.assertRaises(ValueError): policy.quality_checks(dict(summary, mean_gain=float('nan')), 'screen20', 20, 0)


if __name__ == '__main__':
    unittest.main()
