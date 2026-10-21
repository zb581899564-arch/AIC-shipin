"""Focused scientific contracts for weak-label rejection and native frame bounds."""
import unittest

from human_targets import ordinal_pair_indices, require_media_admission, validate_mturk


class HumanTargetContracts(unittest.TestCase):
    def test_soft_votes_preserve_order_and_native_duration(self):
        rows = validate_mturk([[[0, 2], [1, 3]], [.2, 1.7]], ['0', '1/25', '2/25'], '3/25',
                             index_convention='ZERO_BASED_HALF_OPEN')
        self.assertEqual(str(rows[-1]['end']), '3/25')
        self.assertEqual(ordinal_pair_indices([r['soft_vote'] for r in rows]), [(1, 0)])

    def test_unknown_and_outside_native_bounds_stop(self):
        for annotation in [[[[0, 4]], [1.]], [[[0, 1]], [float('nan')]], [[[0, 1]], [-1.]]]:
            with self.assertRaises(ValueError):
                validate_mturk(annotation, ['0', '1/25', '2/25'], '3/25',
                               index_convention='ZERO_BASED_HALF_OPEN')

    def test_frame_index_convention_is_not_inferred(self):
        with self.assertRaises(ValueError):
            validate_mturk([[[1, 3]], [1.]], ['0', '1/25', '2/25'], '3/25',
                           index_convention='UNKNOWN')

    def test_missing_source_or_alignment_is_not_a_training_example(self):
        with self.assertRaises(ValueError):
            require_media_admission(dict(target_kind='AUTOMATIC_MATCH_LABEL'))


if __name__ == '__main__':
    unittest.main()
