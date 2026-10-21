"""Small exhaustive mathematical controls for the new reference-only bounds."""
import importlib.util
import itertools
from pathlib import Path
import unittest

import numpy as np

spec = importlib.util.spec_from_file_location("evidence_diagnostic", Path(__file__).with_name("diagnostic.py"))
api = importlib.util.module_from_spec(spec)
spec.loader.exec_module(api)


class OracleChecks(unittest.TestCase):
    def test_common_subset_matches_exhaustive_all_small_matrices(self):
        for bits in itertools.product([False, True], repeat=8):
            labels = np.asarray(bits, dtype=np.bool_).reshape(4, 2)
            for domain in ([0, 1, 2, 3], [0, 2], []):
                expected = max(api.utility([domain[i] for i in range(len(domain)) if mask >> i & 1], labels)
                               for mask in range(1 << len(domain)))
                actual = api.shared_subset_oracle(labels, domain)
                self.assertAlmostEqual(expected, actual["f1"], places=12)

    def test_window_combination_uses_complete_source_denominators(self):
        labels = np.asarray([[1, 1], [1, 0], [0, 1], [0, 0], [0, 1]], dtype=bool)
        windows = [[[], [0], [0, 1], [1]], [[], [2, 3], [4], [2, 4]]]
        expected = max(api.utility(set(a) | set(b), labels) for a, b in itertools.product(*windows))
        actual = api.window_action_oracle(windows, labels)
        self.assertAlmostEqual(expected, actual["f1"], places=12)
        self.assertEqual(16, actual["combinations"])

    def test_overlap_missing_unknown_and_bad_domain_rejected(self):
        labels = np.ones((3, 2), dtype=bool)
        with self.assertRaises(ValueError): api.window_action_oracle([[[0]], [[0, 2]]], labels)
        with self.assertRaises(ValueError): api.window_action_oracle([[]], labels)
        with self.assertRaises(ValueError): api.shared_subset_oracle(labels, [3])
        with self.assertRaises(ValueError): api.utility([], np.ones((3, 2), dtype=float))
        with self.assertRaises(ValueError): api.window_action_oracle([[[], [0]], [[], [1]]], labels, limit=3)

    def test_empty_rater_is_retained_not_cherry_picked(self):
        labels = np.asarray([[0, 1], [0, 1], [0, 0]], dtype=bool)
        self.assertEqual(0.5, api.utility([], labels))
        self.assertEqual(0.5, api.shared_subset_oracle(labels, [0, 1, 2])["f1"])


if __name__ == "__main__":
    unittest.main()
