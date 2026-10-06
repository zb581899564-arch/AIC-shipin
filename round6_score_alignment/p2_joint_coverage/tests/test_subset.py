"""Small, hand-checkable cases for the frozen subset replay rule."""
from __future__ import annotations

import json
import random
import unittest

from aic6.subset import regenerate_subset_bytes


def line(kind: str, frame: int) -> bytes:
    return (json.dumps({"video_id": "v", "source_frame": frame, "kind": kind},
                       sort_keys=True) + "\r\n").encode("utf-8")


class TestSubsetReplay(unittest.TestCase):
    def test_controls_retained_and_gap_draw_in_original_order(self):
        full = (line("NEEDS_INFERENCE", 1) + line("CONTROL_SAME_FRAME", 2)
                + line("NEEDS_INFERENCE", 3) + line("NEEDS_INFERENCE", 4))
        chosen = set(random.Random(7).sample([0, 2, 3], 2))
        original_lines = full.splitlines(keepends=True)
        expected = b"".join(row for i, row in enumerate(original_lines)
                            if i == 1 or i in chosen)
        self.assertEqual(regenerate_subset_bytes(full, seed=7, n_gaps=2), expected)
        self.assertIn(b"\r\n", expected)

    def test_duplicate_key_rejected(self):
        full = line("NEEDS_INFERENCE", 1) + line("CONTROL_SAME_FRAME", 1)
        with self.assertRaises(ValueError):
            regenerate_subset_bytes(full, seed=7, n_gaps=1)

    def test_more_gaps_than_available_rejected(self):
        with self.assertRaises(ValueError):
            regenerate_subset_bytes(line("NEEDS_INFERENCE", 1), seed=7,
                                    n_gaps=2)


if __name__ == "__main__":
    unittest.main()
