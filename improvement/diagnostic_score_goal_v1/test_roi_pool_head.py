"""At most one tiny synthetic optimizer update; no real assets/model/GPU."""
import copy
import io
import unittest

import numpy as np
import torch

from roi_pool import FEATURE_DIM, VISUAL_DIM, candidate_features
from roi_head import (CandidateIoUHead, batch_sequence, calibrate_margin, fit,
                      fit_normalization, normalize_features, predict_scores,
                      select_candidate, source_mean_mse)


def grid(values):
    return np.repeat(np.asarray(values, np.float32)[..., None], 4096, axis=2)


class ROIPoolHeadTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.old_threads = torch.get_num_threads(); torch.set_num_threads(1)

    @classmethod
    def tearDownClass(cls):
        torch.set_num_threads(cls.old_threads)

    def test_uniform_grid_visual_zero_and_geometry(self):
        value = candidate_features(grid([[7, 7], [7, 7]]), [[0, 0, 32]], 32, 18)
        self.assertEqual(value.shape, (1, FEATURE_DIM)); self.assertEqual(value.dtype, np.float32)
        np.testing.assert_array_equal(value[0, :VISUAL_DIM], 0)
        np.testing.assert_allclose(value[0, VISUAL_DIM:], [0, 0, 1, 1, 1, .5, .5, 16/9])

    def test_fractional_cell_area_not_cell_center_membership(self):
        value = candidate_features(grid([[0, 2]]), [[0, 0, 24]], 32, 18)[0]
        self.assertAlmostEqual(float(value[0]), -1/3, places=6)
        self.assertAlmostEqual(float(value[4096]), -4/3, places=6)
        self.assertAlmostEqual(float(value[8192]), 0., places=6)

    def test_actual_row_major_left_right_top_bottom(self):
        # Non-square2x3 coordinate grid: value=10*row+col. Half-width
        # crosses the middle column, whose area must split exactly in half.
        value = candidate_features(grid([[0, 1, 2], [10, 11, 12]]), [[0, 0, 32]], 32, 18)[0]
        self.assertEqual(float(value[0]), 0.)
        self.assertAlmostEqual(float(value[4096]), -4/3, places=6)
        self.assertEqual(float(value[8192]), -10.)

    def test_invalid_grid_or_empty_or_illegal_roi_fails(self):
        bad = grid([[0, 1]]); bad[0, 0, 0] = np.nan
        for value, boxes in [(bad, [[0, 0, 16]]), (np.zeros((0, 1, 4096), np.float32), [[0, 0, 16]]),
                             (grid([[1]]), []), (grid([[1]]), [[-1, 0, 16]])]:
            with self.assertRaises(ValueError): candidate_features(value, boxes, 32, 18)

    def test_pool_does_not_mutate_grid_candidates_or_accept_gt(self):
        value = grid([[0, 1]]); saved = value.copy(); boxes = [[0, 0, 16]]; original = copy.deepcopy(boxes)
        candidate_features(value, boxes, 32, 18)
        np.testing.assert_array_equal(value, saved); self.assertEqual(boxes, original)
        with self.assertRaises(TypeError): candidate_features(value, boxes, 32, 18, targets=[1.])

    def test_head_actual_parameter_count_and_sigmoid_range(self):
        model = CandidateIoUHead()
        self.assertEqual(model.parameter_count, 393537)
        score = model(torch.zeros((2, FEATURE_DIM), dtype=torch.float32))
        self.assertTrue(bool(((score >= 0) & (score <= 1)).all()))

    def test_train_only_norm_and_control_zero_after_normalization(self):
        x = np.stack([np.ones(FEATURE_DIM), np.ones(FEATURE_DIM)*3]).astype(np.float32)
        sources = {'train': {'features': x}, 'dev': {'features': x*10000}}
        norm = fit_normalization(sources, ['train'])
        np.testing.assert_array_equal(norm['mean'], 2.)
        control = normalize_features(x, norm, 'GEOMETRY_CONTROL')
        np.testing.assert_array_equal(control[:, :VISUAL_DIM], 0.)
        np.testing.assert_array_equal(control[:, VISUAL_DIM:], [[-1]*8, [1]*8])

    def test_source_mse_not_candidate_count_weighted(self):
        pred = torch.tensor([1., 0., 0., 0.]); target = torch.zeros(4)
        self.assertEqual(float(source_mean_mse(pred, target, [1, 3])), .5)
        a, ha = batch_sequence(['a', 'b'], 1); b, hb = batch_sequence(['a', 'b'], 1)
        np.testing.assert_array_equal(a, b); self.assertEqual(ha, hb)

    def test_single_synthetic_update_gradient_and_weight_reload(self):
        rng = np.random.default_rng(5)
        sources = {sid: {'features': rng.normal(size=(n, FEATURE_DIM)).astype(np.float32),
                         'targets': np.linspace(.1, .9, n, dtype=np.float32)} for sid, n in [('a', 2), ('b', 3)]}
        model, norm, report = fit(sources, ['a', 'b'], updates=1)
        self.assertGreater(report['gradient_norm_history'][0], 0)
        self.assertEqual(report['updates'], 1); self.assertTrue(report['synthetic_interface_check_only'])
        buffer = io.BytesIO(); torch.save(model.state_dict(), buffer); buffer.seek(0)
        restored = CandidateIoUHead(); restored.load_state_dict(torch.load(buffer, weights_only=True))
        np.testing.assert_array_equal(predict_scores(model, norm, sources['a']['features']),
                                      predict_scores(restored, norm, sources['a']['features']))

    def test_fixed_source_max_quantile_rank109_without_interpolation(self):
        scores = {str(i): np.array([0., i/2000], np.float64) for i in range(1, 121)}
        targets = {sid: np.zeros(2, np.float32) for sid in scores}
        result = calibrate_margin(scores, targets)
        self.assertEqual(result['order_statistic_rank_one_based'], 109)
        self.assertAlmostEqual(result['threshold'], 109/2000)

    def test_strict_margin_ties_keep_baseline_and_worst_candidate_calibration(self):
        self.assertEqual(select_candidate([.25, .75], .5), 0)
        self.assertEqual(select_candidate([.25, .7501], .5), 1)
        self.assertEqual(select_candidate([.75, .75], 0.), 0)
        scores = {str(i): np.array([.5, .9, .8]) for i in range(120)}
        targets = {sid: np.array([.5, .85, .4], np.float32) for sid in scores}
        self.assertAlmostEqual(calibrate_margin(scores, targets)['threshold'], .4, places=6)

    def test_missing_calibration_or_nonfinite_selection_never_falls_back(self):
        with self.assertRaises(ValueError): calibrate_margin({'a': [.5]}, {'a': np.array([.5], np.float32)})
        with self.assertRaises(ValueError): select_candidate([.5, np.nan], .1)
        with self.assertRaises(ValueError): select_candidate([.5, .7], -.1)


if __name__ == '__main__':
    unittest.main()
