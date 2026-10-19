import unittest
from fractions import Fraction
from qvh_query_saliency_bridge import certified_range, query_clip_records


class BridgeTests(unittest.TestCase):
    def test_certified_interval_interior_including_fractional_fps(self):
        for fps in [(30, 1), (30000, 1001), (25, 1)]:
            lo, hi = certified_range(2, 4, *fps, 0.003, 1000)
            epsilon = Fraction('0.003001')
            for i in range(lo, hi):
                t = Fraction(i * fps[1], fps[0])
                self.assertGreaterEqual(t - epsilon, 2)
                self.assertLess(t + epsilon, 4)
            self.assertLess(Fraction((lo - 1) * fps[1], fps[0]) - epsilon, 2)
            self.assertGreaterEqual(Fraction(hi * fps[1], fps[0]) + epsilon, 4)

    def test_uncertain_or_outside_source_is_not_filled(self):
        self.assertIsNone(certified_range(0, 2, 30, 1, 1.1, 500))
        self.assertIsNone(certified_range(20, 22, 30, 1, 0.001, 500))

    def fixture(self):
        parent = dict(parent_sample_id='p', source_path='/data/abcdefghijk_0.0_10.0.mp4',
                      source_sha256='a' * 64, n_frames=300, fps_num=30, fps_den=1,
                      registered_windows=[dict(window_id='w0', clip_start_sec=0, clip_end_sec=8),
                                          dict(window_id='w1', clip_start_sec=0, clip_end_sec=8)])
        old = dict(sample_id='p', source_path=parent['source_path'], decoded_source_frames=300,
                   pts_audit_status='PASS', pts_max_residual_sec=0.001)
        row = dict(vid='abcdefghijk_0.0_10.0', qid=1, query='A person jumps.', duration=9,
                   relevant_clip_ids=[1, 4], saliency_scores=[[0, 1, 4], [4, 3, 2]])
        return parent, old, row

    def test_preserves_query_votes_and_does_not_label_unselected(self):
        records, skipped = query_clip_records(*self.fixture())
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]['query'], 'A person jumps.')
        self.assertEqual(records[0]['original_rater_scores'], [0, 1, 4])
        self.assertEqual(records[0]['existing_window_ids'], ['w0', 'w1'])
        self.assertFalse(records[0]['training_admitted'])
        self.assertEqual(records[0]['clip_id'], 1)
        self.assertEqual(skipped['clip_not_wholly_inside_author_duration'], 1)

    def test_identity_mismatch_rejected(self):
        parent, old, row = self.fixture()
        old['decoded_source_frames'] = 299
        with self.assertRaises(ValueError):
            query_clip_records(parent, old, row)


if __name__ == '__main__':
    unittest.main()
