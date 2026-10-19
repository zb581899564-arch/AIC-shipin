import copy
import io
import unittest
import numpy as np

import crop_gain_math_v45 as gain


def geometry(x):
    a = np.zeros(13, np.float64); a[0] = 1.; a[1] = x; a[12] = .25
    return a


def sources():
    rows = []
    for sid in range(3):
        pairs = []
        for j in range(2):
            x = np.arange(1, 15, dtype=np.float64)*(sid+1)*(j+1)
            x[6] = 0.
            pairs.append(dict(pair=[0, j+1], x14=x, target=.1*(sid+1)-.03*j))
        rows.append(dict(source_id='source%d'%sid, pairs=pairs))
    return rows


class GainTests(unittest.TestCase):
    def test_exact14_raw_margin_tie_inconsistency_geometry(self):
        f = np.array([1., 3., 2.]); r = np.array([4., 1., 2.])
        a, b = geometry(.1), geometry(.7)
        actual = gain.pair_features(f, r, a, b)
        pf = np.exp(f-f.max()); pf /= pf.sum(); pr = np.exp(r-r.max()); pr /= pr.sum()
        s = 2.5; t = (pf[2]+pr[2])/2; u = np.abs(pf-pr[[1, 0, 2]]).sum()/2
        expected = np.r_[s, s*t, s*u, (b-a)[1:12]]
        np.testing.assert_array_equal(actual, expected)
        self.assertEqual(actual.shape, (14,))

    def test_swap_exact_negative_and_self_exact_positive_zero(self):
        rng = np.random.default_rng(20261018)
        for _ in range(50):
            f, r = rng.normal(size=(2, 3))*10; a, b = geometry(.1), geometry(.9)
            x = gain.pair_features(f, r, a, b)
            np.testing.assert_array_equal(gain.pair_features(r, f, b, a), -x)
        raw = [20., -9., 4.]
        own = gain.pair_features(raw, raw, a, a)
        np.testing.assert_array_equal(own.view(np.uint64), np.zeros(14, np.uint64))
        with self.assertRaises(ValueError): gain.pair_features(raw, [21., -9., 4.], a, a)

    def test_extreme_logits_stable_and_unknowns_rejected(self):
        self.assertTrue(np.isfinite(gain.pair_features([10000., -10000., 0.], [-10000., 10000., 0.], geometry(0), geometry(1))).all())
        for bad in ([True, 1., 2.], [np.nan, 1., 2.], [np.inf, 1., 2.], [1., 2.]):
            with self.assertRaises(ValueError): gain.pair_features(bad, [0., 0., 0.], geometry(0), geometry(1))
        wrong = geometry(1); wrong[12] += 1
        with self.assertRaises(ValueError): gain.pair_features([1, 2, 3], [3, 2, 1], geometry(0), wrong)

    def test_source_equal_rms_and_all_three_closed_form_solves(self):
        rows = sources(); state, report = gain.fit(rows)
        x = np.stack([p['x14'] for s in rows for p in s['pairs']]); y = np.array([p['target'] for s in rows for p in s['pairs']])
        weights = np.full(6, 1/6); rms = np.sqrt(weights@(x*x)); rms[rms == 0] = 1.
        np.testing.assert_array_equal(state['RMS'], rms)
        for arm, columns in [('JOINT14', slice(None)), ('GEOM11', slice(3, 14)), ('MARGIN1', slice(0, 1))]:
            a = (x/rms)[:, columns]
            expected = np.linalg.solve(a.T@(weights[:, None]*a)+.01*np.eye(a.shape[1]), a.T@(weights*y))
            np.testing.assert_array_equal(state[arm+'_beta'], expected)
        self.assertEqual(report['solves'], 3); self.assertEqual(report['unordered_pairs'], 6)
        self.assertEqual(report['primary'], 'JOINT14'); self.assertTrue(report['source_equal_pair_mean'])

    def test_no_centering_no_intercept_and_fixed_controls(self):
        rows = sources(); state, report = gain.fit(rows)
        shifted = copy.deepcopy(rows)
        for source in shifted:
            for pair in source['pairs']: pair['target'] += .1
        other, _ = gain.fit(shifted)
        self.assertFalse(np.array_equal(state['JOINT14_beta'], other['JOINT14_beta']))
        self.assertFalse(report['source_centered_targets']); self.assertFalse(report['intercept'])
        predictions = gain.predict(state, np.zeros((1, 14)))
        for values in predictions.values(): np.testing.assert_array_equal(values, [0.])
        x = np.stack([rows[0]['pairs'][0]['x14']]); p = gain.predict(state, x)
        np.testing.assert_array_equal(p['GEOM11'], (x/state['RMS'])[:, 3:]@state['GEOM11_beta'])
        np.testing.assert_array_equal(p['MARGIN1'], (x/state['RMS'])[:, :1]@state['MARGIN1_beta'])
        self.assertFalse(report['MARGIN1_package_eligible'])
        self.assertTrue(report['MARGIN1_positive_beta_same_sign_as_raw_margin'])

    def test_flat_state_numpy_roundtrip_and_predict_swap(self):
        state, _ = gain.fit(sources()); buffer = io.BytesIO()
        self.assertTrue(all(isinstance(v, np.ndarray) for v in state.values()))
        np.savez(buffer, **state); buffer.seek(0)
        with np.load(buffer, allow_pickle=False) as loaded: restored = {k: loaded[k].copy() for k in loaded.files}
        x = np.stack([p['x14'] for source in sources() for p in source['pairs']])
        a, b, negative = gain.predict(state, x), gain.predict(restored, x), gain.predict(state, -x)
        for arm in gain.ARMS:
            np.testing.assert_array_equal(a[arm].view(np.uint8), b[arm].view(np.uint8))
            np.testing.assert_array_equal(negative[arm], -a[arm])
        self.assertEqual(gain.predict(state, np.empty((0, 14)))['JOINT14'].shape, (0,))
        wrong = dict(state, version=np.array(1.5))
        with self.assertRaises(ValueError): gain.predict(wrong, x)

    def test_target_and_source_grouping_fail_closed(self):
        for kind in ('duplicate_source', 'one_pair', 'mirror', 'repeat_pair', 'unknown_target', 'range', 'screen', 'wrong_original'):
            rows = copy.deepcopy(sources())
            if kind == 'duplicate_source': rows[1]['source_id'] = rows[0]['source_id']
            elif kind == 'one_pair': rows[0]['pairs'].pop()
            elif kind == 'mirror': rows[0]['pairs'][0]['pair'] = [1, 0]
            elif kind == 'repeat_pair': rows[0]['pairs'][1]['pair'] = [0, 1]
            elif kind == 'unknown_target': rows[0]['pairs'][0]['target'] = True
            elif kind == 'range': rows[0]['pairs'][0]['target'] = 1.01
            elif kind == 'screen': rows[0]['role'] = 'screen'
            else: rows[0]['pairs'][0].update(iou_A=.2, iou_B=.2)
            with self.subTest(kind=kind), self.assertRaises(ValueError): gain.fit(rows)
        rows = sources(); rows[0]['pairs'][0].update(iou_A=0., iou_B=rows[0]['pairs'][0]['target'])
        gain.fit(rows)

    def test_strict_positive_baseline_ties_and_bad_predictions(self):
        self.assertEqual(gain.choose_pool([0., -.1, 0.])['selected_index'], 0)
        self.assertEqual(gain.choose_pool([.2, .2, 0.], 2)['selected_index'], 0)
        self.assertEqual(gain.choose_pool([0., 0., 0.], 2)['selected_index'], 2)
        self.assertTrue(gain.choose_pool([0., 1e-20])['changed'])
        for values, baseline in [([.1, .2], 0), ([0., np.nan], 0), ([0.], 1), ([False, .1], 0)]:
            with self.assertRaises(ValueError): gain.choose_pool(values, baseline)

    def test_fixed_screen_confirm_gates_and_controls_cannot_become_primary(self):
        for phase, count, improvement, mean in [('screen20', 20, 5, .01), ('confirm19', 19, 3, .005)]:
            summary = dict(sources=count, improved=improvement, changed=improvement, mean_gain=mean,
                           worst_loss=.1, mean_selected_iou=.8)
            okay = gain.quality_checks(summary, phase, count, 0, .79, .78)
            self.assertTrue(okay['admitted']); self.assertEqual(okay['primary'], 'JOINT14')
            for patch in ({'mean_gain': 0.}, {'improved': improvement-1}, {'worst_loss': .1001}, {'sources': count-1}):
                changed = dict(summary, **patch)
                zeros = min(count, changed['sources'])
                self.assertFalse(gain.quality_checks(changed, phase, zeros, 0, .79, .78)['admitted'])
            self.assertFalse(gain.quality_checks(summary, phase, count-1, 0, .79, .78)['admitted'])
            self.assertFalse(gain.quality_checks(summary, phase, count, 1, .79, .78)['admitted'])
            self.assertFalse(gain.quality_checks(summary, phase, count, 0, .8, .78)['admitted'])
            self.assertFalse(gain.quality_checks(summary, phase, count, 0, .79, .8)['admitted'])


if __name__ == '__main__':
    unittest.main()
