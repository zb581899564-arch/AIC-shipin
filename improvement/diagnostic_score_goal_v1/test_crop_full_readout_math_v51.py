import io
import unittest
from unittest import mock

import numpy as np

import crop_full_readout_math_v51 as readout


class FullReadoutTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        # Synthetic1204x4096 input has48 active columns. Only the expensive
        # zero-padded SVD is replaced by its equivalent active-column SVD.
        # Actual thin-SVD/sign/rank behavior is separately tested below.
        rng = np.random.default_rng(20261018)
        active = rng.normal(size=(1204, 48)) + np.linspace(0., .5, 48)
        cls.x = np.zeros((1204, 4096), np.float64); cls.x[:, :48] = active
        cls.g = rng.normal(size=(1204, 11))
        cls.digits = rng.normal(size=(1204, 3))
        cls.rows = []
        for i in range(602):
            pairs = []
            for j in range(2):
                row = 2*i+j; ia = .5; ib = ia+.05*np.tanh(active[row, 0])
                pairs.append(dict(pair=[0, j+1], x4096=cls.x[row], geometry_delta11=cls.g[row],
                                  digit_delta3=cls.digits[row], target=ib-ia, iou_A=ia, iou_B=ib))
            cls.rows.append(dict(source_id='s%03d'%i, role='train', pairs=pairs))
        original_svd = np.linalg.svd

        def sparse_equivalent(a, full_matrices=False):
            if a.shape != (1204, 4096):
                return original_svd(a, full_matrices=full_matrices)
            assert full_matrices is False and not np.any(a[:, 48:])
            u, s, vt = original_svd(a[:, :48], full_matrices=False)
            # Complete the zero singular-vector portion without changing any
            # of the retained32 components or their singular values.
            all_s = np.r_[s, np.zeros(1204-len(s))]
            all_vt = np.zeros((1204, 4096)); all_vt[:48, :48] = vt
            all_vt[np.arange(48, 1204), np.arange(48, 1204)] = 1.
            return u, all_s, all_vt

        with mock.patch.object(np.linalg, 'svd', side_effect=sparse_equivalent) as svd, \
                mock.patch.object(np.linalg, 'solve', wraps=np.linalg.solve) as solve:
            cls.state, cls.report = readout.fit(cls.rows)
            cls.svd_calls, cls.solve_calls = svd.call_count, solve.call_count

    def test_fit_source_equal_two_fixed_solves_and_no_centering(self):
        state, report = self.state, self.report
        self.assertEqual((self.svd_calls, self.solve_calls), (1, 2))
        self.assertEqual((report['sources'], report['unordered_pairs']), (602, 1204))
        self.assertEqual(report['primary'], 'FULL43'); self.assertTrue(report['source_equal_pair_mean'])
        self.assertFalse(report['PCA_centering']); self.assertFalse(report['source_centered_targets'])
        self.assertFalse(report['intercept']); self.assertFalse(report['smoothing'])
        weights = np.full(1204, 1/1204)
        rms = np.sqrt(weights@(self.x*self.x)); rms[rms == 0] = 1.
        np.testing.assert_array_equal(state['RMS4096'], rms)
        np.testing.assert_array_equal(state['RMS4096'][48:], np.ones(4048))
        joined = np.column_stack(((self.x/rms)@state['PCA32'].T, self.g))
        rms43 = np.sqrt(weights@(joined*joined)); rms43[rms43 == 0] = 1.
        np.testing.assert_array_equal(state['RMS43'], rms43)
        a = joined/rms43; y = np.array([p['target'] for s in self.rows for p in s['pairs']])
        for arm, design in [('FULL43', a), ('GEOM11', a[:, 32:])]:
            expected = np.linalg.solve(design.T@(weights[:, None]*design)+.01*np.eye(design.shape[1]),
                                       design.T@(weights*y))
            np.testing.assert_array_equal(state[arm+'_beta'], expected)
            self.assertAlmostEqual(report['arms'][arm]['train_source_equal_MSE'],
                                   float(weights@((design@expected-y)**2)))
        self.assertEqual(report['diagnostic_only_arrays'], ['singular_values'])
        self.assertEqual(state['singular_values'].shape, (1204,))
        self.assertTrue(all(isinstance(value, np.ndarray) and value.dtype.kind in 'fi' for value in state.values()))

    def test_nuisance_rank_qr_and_legitimate_stop(self):
        rng = np.random.default_rng(8); x = rng.normal(size=(40, 48)); before = x.copy()
        d = rng.normal(size=40); digits = np.column_stack((d, 2*d, np.zeros(40)))
        diagnostic = readout._outside_nuisance_diagnostic(x, digits)
        self.assertEqual(diagnostic['nuisance_QR_rank'], 2)
        self.assertGreater(diagnostic['residual_energy_ratio'], 1e-6)
        self.assertFalse(diagnostic['projection_applied_to_features'])
        np.testing.assert_array_equal(x, before)
        nuisance_only = d[:, None]*np.arange(1., 49.)
        with self.assertRaises(readout.ReadoutStop) as caught:
            readout._outside_nuisance_diagnostic(nuisance_only, digits)
        self.assertLessEqual(caught.exception.diagnostics['residual_energy_ratio'], 1e-6)
        self.assertFalse(caught.exception.diagnostics['SVD_computed'])
        with self.assertRaises(ValueError) as bad:
            readout._outside_nuisance_diagnostic(np.full((40, 48), np.nan), digits)
        self.assertNotIsInstance(bad.exception, readout.ReadoutStop)

    def test_real_small_uncentered_svd_sign_and_fixed32_structural_gates(self):
        a = np.zeros((40, 48)); a[np.arange(40), np.arange(40)] = -np.linspace(40., 1., 40)
        components, singular, diagnostic = readout._pca32(a, {})
        self.assertEqual(components.shape, (32, 48)); self.assertEqual(diagnostic['numerical_rank'], 40)
        np.testing.assert_allclose(singular, np.arange(40., 0., -1.), rtol=2e-15, atol=0.)
        for row in components:
            self.assertGreater(row[np.argmax(np.abs(row))], 0.)
        np.testing.assert_allclose((a@components.T).T@(a@components.T), np.diag(singular[:32]**2), rtol=2e-15, atol=0.)
        for values in (np.r_[np.ones(31), np.zeros(9)], np.r_[np.ones(31), 1e-6, np.zeros(8)]):
            weak = np.zeros((40, 48)); weak[np.arange(40), np.arange(40)] = values
            with self.subTest(s32=values[31]), self.assertRaises(readout.ReadoutStop) as caught:
                readout._pca32(weak, {})
            self.assertTrue(caught.exception.diagnostics['SVD_computed'])
            self.assertEqual(caught.exception.diagnostics['required_components'], 32)

    def test_numeric_state_roundtrip_swap_and_self_exact_zero(self):
        buffer = io.BytesIO(); np.savez(buffer, **self.state); buffer.seek(0)
        with np.load(buffer, allow_pickle=False) as saved:
            restored = {key: saved[key].copy() for key in saved.files}
        for key in self.state:
            self.assertEqual(self.state[key].dtype, restored[key].dtype)
            self.assertEqual(self.state[key].shape, restored[key].shape)
            self.assertEqual(self.state[key].tobytes(), restored[key].tobytes())
        x, g = self.x[:4], self.g[:4]
        a, b = readout.predict(self.state, x, g), readout.predict(restored, x, g)
        swapped = readout.predict(self.state, -x, -g)
        for arm in readout.ARMS:
            np.testing.assert_array_equal(a[arm].view(np.uint8), b[arm].view(np.uint8))
            np.testing.assert_array_equal(swapped[arm], -a[arm])
            zero = readout.predict(self.state, np.zeros((1, 4096)), np.zeros((1, 11)))[arm]
            np.testing.assert_array_equal(zero.view(np.uint64), [0])
        self.assertEqual(readout.predict(self.state, np.empty((0, 4096)), np.empty((0, 11)))['FULL43'].shape, (0,))
        geometry_expected = (g/self.state['RMS43'][32:])@self.state['GEOM11_beta']
        np.testing.assert_array_equal(a['GEOM11'], geometry_expected)

    def test_grouping_target_and_eval_isolation_fail_closed(self):
        for kind in ('count', 'duplicate', 'one_pair', 'mirror', 'repeat', 'target', 'original', 'screen'):
            rows = list(self.rows); source = dict(rows[0]); source['pairs'] = [dict(p) for p in source['pairs']]; rows[0] = source
            if kind == 'count': rows.pop()
            elif kind == 'duplicate': rows[1] = dict(rows[1], source_id=rows[0]['source_id'])
            elif kind == 'one_pair': source['pairs'].pop()
            elif kind == 'mirror': source['pairs'][0]['pair'] = [1, 0]
            elif kind == 'repeat': source['pairs'][1]['pair'] = [0, 1]
            elif kind == 'target': source['pairs'][0]['target'] = True
            elif kind == 'original': source['pairs'][0]['target'] *= -1
            else: source['role'] = 'screen'
            with self.subTest(kind=kind), self.assertRaises(ValueError):
                readout._source_rows(rows)

    def test_nonfinite_wrong_shape_unknown_values_are_engineering_errors(self):
        cases = [(self.state, np.zeros((1, 4095)), np.zeros((1, 11))),
                 (self.state, np.full((1, 4096), np.inf), np.zeros((1, 11))),
                 (dict(self.state, RMS4096=np.zeros(4096)), self.x[:1], self.g[:1]),
                 (dict(self.state, ridge=np.array(.1)), self.x[:1], self.g[:1])]
        for state, x, g in cases:
            with self.subTest(shape=np.shape(x)), self.assertRaises(ValueError) as caught:
                readout.predict(state, x, g)
            self.assertNotIsInstance(caught.exception, readout.ReadoutStop)
        for gains in ([False, .1], [0., np.nan], [.1, .2]):
            with self.assertRaises(ValueError): readout.choose_pool(gains)

    def test_strict_positive_selection_exact_ties_and_required_new_action(self):
        self.assertEqual(readout.choose_pool([0., -.1, 0.])['selected_index'], 0)
        self.assertEqual(readout.choose_pool([.2, .2, 0.], 2)['selected_index'], 0)
        self.assertEqual(readout.choose_pool([0., 0., 0.], 2)['selected_index'], 2)
        self.assertTrue(readout.choose_pool([0., 1e-20])['changed'])
        for phase, count, improved, gain in [('screen20', 20, 5, .01), ('confirm19', 19, 3, .005)]:
            summary = dict(sources=count, improved=improved, changed=improved, mean_gain=gain,
                           worst_loss=.1, mean_selected_iou=.8)
            result = readout.quality_checks(summary, phase, count, 0, .79, .78, True)
            self.assertTrue(result['admitted']); self.assertEqual(result['primary'], 'FULL43')
            for args in [(count, 0, .79, .78, False), (count, 0, .8, .78, True),
                         (count, 0, .79, .8, True), (count-1, 0, .79, .78, True),
                         (count, 1, .79, .78, True)]:
                self.assertFalse(readout.quality_checks(summary, phase, *args)['admitted'])
            rejected = dict(summary, improved=0, changed=0, mean_gain=0.)
            self.assertFalse(readout.quality_checks(rejected, phase, count, 0, .79, .78, True)['admitted'])
        with self.assertRaises(ValueError):
            readout.quality_checks(summary, phase, count, 0, .79, .78, None)


if __name__ == '__main__':
    unittest.main()
