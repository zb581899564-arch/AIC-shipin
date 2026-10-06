import unittest

import build_qvh_v2 as qvh


class QvhV2PureTests(unittest.TestCase):
    def test_source_group_uses_right_split(self):
        self.assertEqual(qvh.source_group("abc_def_60.0_210.0"), "abc_def")

    def test_video_shard_is_lowercase(self):
        self.assertEqual(qvh.video_path_for(qvh.Path("/videos"), "Wabc_0.0_10.0").parts[-2:], ("w", "Wabc_0.0_10.0.mp4"))

    def test_annotation_window_bounds(self):
        row = {
            "qid": 1,
            "query": "event",
            "duration": 10,
            "vid": "abc_0.0_10.0",
            "relevant_clip_ids": [4],
            "saliency_scores": [[3, 4, 2]],
            "relevant_windows": [[8, 11]],
        }
        self.assertIn("RELEVANT_WINDOW_OUT_OF_BOUNDS", qvh.annotation_errors(row))

    def test_window_contract_rejects_more_than_four_unordered_or_overlap(self):
        base = {
            "qid": 1,
            "query": "event",
            "duration": 20,
            "vid": "abc_0.0_20.0",
            "relevant_clip_ids": [],
            "saliency_scores": [],
        }
        self.assertNotIn("INVALID_RELEVANT_WINDOWS", qvh.annotation_errors({**base, "relevant_windows": []}))
        self.assertIn("TOO_MANY_RELEVANT_WINDOWS", qvh.annotation_errors({**base, "relevant_windows": [[0, 1], [2, 3], [4, 5], [6, 7], [8, 9]]}))
        self.assertIn("UNORDERED_RELEVANT_WINDOWS", qvh.annotation_errors({**base, "relevant_windows": [[4, 5], [2, 3]]}))
        self.assertIn("OVERLAPPING_RELEVANT_WINDOWS", qvh.annotation_errors({**base, "relevant_windows": [[2, 5], [4, 6]]}))

    def test_saliency_is_unmerged_diagnostic_2s(self):
        row = {
            "duration": 7,
            "relevant_clip_ids": [0, 1, 3],
            "saliency_scores": [[3, 3, 1], [2, 2, 4], [4, 4, 3]],
        }
        self.assertEqual(qvh.saliency_segments_2s(row), [[0.0, 2.0], [6.0, 7.0]])

    def test_diagnostic_saliency_only_is_clipped_to_media(self):
        self.assertEqual(qvh.clip_diagnostic_segments([[2.0, 4.0]], 3.5), ([[2.0, 3.5]], 1))

    def test_val_partition_is_group_disjoint_and_deterministic(self):
        rows = [
            {"vid": f"source_{group}_0.0_10.0", "qid": group * 10 + i}
            for group in range(12)
            for i in range(2)
        ]
        dev1, hold1 = qvh.partition_val_groups(rows, 42)
        dev2, hold2 = qvh.partition_val_groups(rows, 42)
        self.assertEqual(dev1, dev2)
        self.assertEqual(hold1, hold2)
        self.assertFalse({qvh.source_group(x["vid"]) for x in dev1} & {qvh.source_group(x["vid"]) for x in hold1})

    def test_preview_group_is_forced_dev_only(self):
        rows = [
            {"vid": "wUgPzvcKK5c_0.0_10.0", "qid": 1},
            {"vid": "other_0.0_10.0", "qid": 2},
        ]
        dev, holdout = qvh.partition_val_groups(rows, 42)
        self.assertIn("wUgPzvcKK5c", {qvh.source_group(x["vid"]) for x in dev})
        self.assertNotIn("wUgPzvcKK5c", {qvh.source_group(x["vid"]) for x in holdout})

    def test_training_row_keeps_targets_separate_and_fail_closed(self):
        ann = {
            "qid": 9,
            "vid": "abc_0.0_10.0",
            "query": "person enters",
            "duration": 10,
            "relevant_windows": [[2, 5]],
            "relevant_clip_ids": [1],
            "saliency_scores": [[3, 3, 3]],
        }
        media = {
            "video_path": "/data/a.mp4",
            "video_sha256": "a" * 64,
            "duration_sec": 10.0,
            "fps": 30.0,
            "n_frames": 300,
        }
        row = qvh.training_row(ann, media, "train", trusted=False)
        self.assertEqual(row["answer"], {"segments": [[2.0, 5.0]]})
        self.assertEqual(row["saliency_segments"], [[2.0, 4.0]])
        self.assertEqual(row["video_id"], "qvh_9")
        self.assertEqual(row["source_vid"], "abc_0.0_10.0")
        self.assertEqual(row["video_id"], "qvh_9")
        self.assertFalse(row["trusted_identity"])
        self.assertTrue(row["candidate_only"])


if __name__ == "__main__":
    unittest.main()
