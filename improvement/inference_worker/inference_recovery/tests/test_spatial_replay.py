from __future__ import annotations

import unittest

from inference_recovery.spatial_replay import validate_temporal_for_media, validate_temporal_row


def valid_row():
    return {
        "video_id": "1",
        "source_group": "source",
        "segments_sec": [[1.0, 2.0]],
        "segments_frames": [[24, 48]],
        "status": "ok",
        "timing": {"total_sec": 1.0, "stage1_sec": 1.0, "stage2_sec": 0.0},
        "VRAM": {"peak_mib": 0.0},
        "sampling": [],
        "policy": "multi",
        "query": None,
        "adapter": None,
        "constrained_json": True,
        "constraint_backend": "regex",
        "metadata": {"n_frames": 100, "fps": 24.0, "width": 640, "height": 360},
    }


class TemporalContractTests(unittest.TestCase):
    def test_accepts_frozen_frame_intervals_without_requantization(self):
        row = validate_temporal_row(valid_row())
        seconds, frames = validate_temporal_for_media(
            row,
            item={"video_id": "1", "source_group": "source"},
            n_frames=100,
            fps=24.0,
            width=640,
            height=360,
        )
        self.assertEqual(seconds, [(1.0, 2.0)])
        self.assertEqual(frames, [(24, 48)])

    def test_rejects_wrong_policy_query_adapter_or_constraint(self):
        for key, value in (("policy", "single"), ("query", "text"), ("adapter", "x"), ("constrained_json", False)):
            row = valid_row()
            row[key] = value
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_temporal_row(row)

    def test_rejects_reversed_overlapping_and_out_of_bounds_frames(self):
        for segments in ([[5, 4]], [[1, 5], [4, 8]], [[90, 101]]):
            row = valid_row()
            row["segments_frames"] = segments
            if len(segments) != len(row["segments_sec"]):
                row["segments_sec"] = [[float(i), float(i + 0.5)] for i in range(len(segments))]
            with self.subTest(segments=segments), self.assertRaises(ValueError):
                checked = validate_temporal_row(row)
                validate_temporal_for_media(
                    checked,
                    item={"video_id": "1", "source_group": "source"},
                    n_frames=100,
                    fps=24.0,
                    width=640,
                    height=360,
                )

    def test_valid_empty_requires_both_segment_lists_empty(self):
        row = valid_row()
        row.update(status="valid_empty", segments_sec=[], segments_frames=[])
        self.assertEqual(validate_temporal_row(row)["status"], "valid_empty")
        row["segments_frames"] = [[1, 2]]
        with self.assertRaises(ValueError):
            validate_temporal_row(row)


if __name__ == "__main__":
    unittest.main()
