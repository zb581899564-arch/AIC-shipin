"""CPU regressions for malformed native domains and erased label unknowns.

Only NumPy and the pure helpers are used. No historical result, media, model,
training routine or output directory is opened by these tests.
"""
import importlib.util
from pathlib import Path
import sys
import unittest

import numpy as np


def _load_helpers():
    directory = Path(__file__).resolve().parent
    previous_path = sys.path[:]
    previous_common = sys.modules.get('common')
    previous_provenance = sys.modules.get('provenance')
    try:
        # Public code and deployed code have different parent directories.
        # Resolve the actual retained helper explicitly for this CPU test.
        sys.path.insert(0, str(directory.parent))
        spec = importlib.util.spec_from_file_location('_i3d_common_metric_test', directory / 'common.py')
        common = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(common)
        sys.modules['common'] = common
        spec = importlib.util.spec_from_file_location('_i3d_audit_metric_test', directory / 'audit.py')
        audit = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(audit)
        return common, audit
    finally:
        sys.path[:] = previous_path
        for name, old in (('common', previous_common), ('provenance', previous_provenance)):
            if old is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = old


common, audit = _load_helpers()


class NativeMetricContracts(unittest.TestCase):
    def test_unequal_last_cell_preserves_exact_budget_and_native_tie_order(self):
        bounds, samples, groups = common.native_cells(129)
        self.assertEqual(bounds[-1], (128, 129))
        self.assertEqual(samples[-1].tolist(), [128] * 8)
        selected = common.rank_mask([1., 2., 3.], groups, 3)
        self.assertEqual(np.flatnonzero(selected).tolist(), [64, 65, 128])
        self.assertFalse(common.rank_mask([1., 2., 3.], groups, 0).any())
        self.assertTrue(common.rank_mask([1., 2., 3.], groups, 129).all())

    def test_negative_cell_index_cannot_silently_wrap_to_last_score(self):
        with self.assertRaises(ValueError):
            common.rank_mask([0., 5.], [-1, 0], 1)

    def test_integer_score_extremes_rank_without_overflow_or_float_rounding(self):
        for scores in (np.array([0, 255], dtype=np.uint8),
                       np.array([-128, 127], dtype=np.int8),
                       np.array([2**63, 2**63 + 1], dtype=np.uint64)):
            with self.subTest(dtype=scores.dtype):
                self.assertEqual(common.rank_mask(scores, [0, 1, 1], 1).tolist(),
                                 [False, True, False])
                _, _, groups = common.native_cells(128)
                baseline = np.arange(128) == 0
                labels = (np.arange(128) == 64)[:, None]
                selected = common.rank_mask(scores, groups, 1)
                self.assertEqual(np.flatnonzero(selected).tolist(), [64])
                self.assertEqual(common.mean_pair_f1(selected, labels), 1.)
                self.assertEqual(audit.manual_f1(scores, baseline, labels), 1.)

    def test_noninteger_bool_outside_or_matrix_groups_are_rejected(self):
        for groups in ([0., 1.], [True, False], [0, 2], [[0, 1]], []):
            with self.subTest(groups=groups), self.assertRaises(ValueError):
                common.rank_mask([0., 5.], groups, 1)

    def test_invalid_scores_or_coverage_are_rejected_before_ranking(self):
        for scores in ([float('nan'), 1.], [0., float('inf')], [[0., 1.]], ['0', '1'], []):
            with self.subTest(scores=scores), self.assertRaises(ValueError):
                common.rank_mask(scores, [0, 1], 1)
        for count in (True, np.bool_(False), 1., -1, 3):
            with self.subTest(count=count), self.assertRaises(ValueError):
                common.rank_mask([0., 1.], [0, 1], count)

    def test_native_domain_count_is_a_positive_integer(self):
        for count in (True, np.bool_(True), 0, -1, 3., float('nan')):
            with self.subTest(count=count), self.assertRaises(ValueError):
                common.native_cells(count)

    def test_invalid_label_cannot_become_a_perfect_positive_match(self):
        for invalid in (float('nan'), float('inf'), -1., 2., .5):
            labels = np.array([[invalid], [0.]])
            with self.subTest(invalid=invalid):
                with self.assertRaises(ValueError):
                    common.mean_pair_f1([True, False], labels)
                with self.assertRaises(ValueError):
                    audit.manual_f1(None, [True, False], labels)

    def test_mask_shape_and_reviewer_domain_are_explicit(self):
        for mask, labels in (([2, 0], [[1], [0]]), ([1, 0], [[1]]),
                             ([[1, 0]], [[1], [0]]), ([0, 0], np.empty((2, 0))),
                             ([], np.empty((0, 1)))):
            with self.subTest(mask=mask, shape=np.asarray(labels).shape):
                with self.assertRaises(ValueError):
                    common.mean_pair_f1(mask, labels)
                with self.assertRaises(ValueError):
                    audit.manual_f1(None, mask, labels)

    def test_unknown_label_masks_cannot_enter_complete_source_metric(self):
        data = dict(baseline=np.array([1, 0]), labels=np.array([[1], [0]]))
        for extra in (dict(known=np.array([[True], [False]])),
                      dict(known=np.array([True, True])),
                      dict(known=np.array([[1], [1]])),
                      dict(known_other=np.array([[True], [True]]))):
            with self.subTest(extra=extra), self.assertRaises(ValueError):
                common.comparison_targets(dict(data, **extra))
        mask, labels = common.comparison_targets(dict(data, known=np.ones((2, 1), dtype=bool)))
        self.assertEqual(mask.dtype, np.bool_)
        self.assertEqual(labels.dtype, np.bool_)

    def test_raw_comparison_labels_are_checked_before_cast(self):
        with self.assertRaises(ValueError):
            common.comparison_targets(dict(baseline=[1, 0], labels=[[float('nan')], [0.]]))

    def test_historical_external_empty_pair_convention_stays_zero(self):
        baseline = np.array([False, False])
        labels = np.array([[False, True], [False, False]])
        self.assertEqual(common.mean_pair_f1(baseline, labels), 0.)
        self.assertEqual(audit.manual_f1(None, baseline, labels), 0.)

    def test_valid_finite_memberships_keep_independent_arithmetic_equal(self):
        rng = np.random.default_rng(20261021)
        _, _, groups = common.native_cells(129)
        for count in (0, 1, 64, 65, 129):
            for _ in range(4):
                scores = rng.normal(size=3)
                baseline = np.arange(129) < count
                labels = rng.integers(0, 2, size=(129, 3), dtype=np.uint8)
                selected = common.rank_mask(scores, groups, np.int64(count))
                self.assertAlmostEqual(common.mean_pair_f1(selected, labels),
                                       audit.manual_f1(scores, baseline, labels), places=15)


if __name__ == '__main__':
    unittest.main()
