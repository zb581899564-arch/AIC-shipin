from __future__ import annotations

import json
import os
import sys
import unittest
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from protected_boundary import (
    ProtectedInputError,
    assert_not_protected,
    assert_reference_payload_absent,
    load_registry,
)


class ProtectedBoundaryTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        run_dir = os.environ.get("P2R9_RUN_DIR")
        if not run_dir:
            raise RuntimeError("P2R9_RUN_DIR is required")
        cls.registry = load_registry(Path(run_dir) / "protected_input_registry.json")
        cls.root = Path(__file__).resolve().parents[3]

    def test_registry_counts_are_frozen(self) -> None:
        categories = {row["name"]: row for row in self.registry["categories"]}
        self.assertEqual(categories["round6_weak_holdout_64"]["count"], 64)
        self.assertEqual(categories["p2r_gnmc_exposed_sealed_4"]["count"], 4)
        self.assertEqual(categories["temporal_round5_historical_holdout_88"]["count"], 88)
        self.assertEqual(self.registry["counts"]["blocked_identity_digests"], 68)

    def test_every_weak_holdout_identity_is_rejected(self) -> None:
        path = self.root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl"
        rejected = 0
        for line in path.read_text(encoding="utf-8").splitlines():
            row = json.loads(line)
            if row.get("split") != "holdout":
                continue
            candidate = {key: row[key] for key in ("row_index", "video_id", "source_vid", "youtube_id")}
            candidate["split"] = "process_sealed_holdout"
            with self.assertRaisesRegex(ProtectedInputError, "protected identity"):
                assert_not_protected(candidate, self.registry)
            rejected += 1
        self.assertEqual(rejected, 64)

    def test_every_exposed_gnmc_identity_is_rejected_without_box_access(self) -> None:
        path = self.root / "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/sealed_holdout_manifest.jsonl"
        import re
        ids = []
        for line in path.read_text(encoding="utf-8").splitlines():
            match = re.search(r'"item_id"\s*:\s*("(?:[^"\\]|\\.)*")', line)
            self.assertIsNotNone(match)
            ids.append(json.loads(match.group(1)))
        for item_id in ids:
            with self.assertRaisesRegex(ProtectedInputError, "protected identity"):
                assert_not_protected({"split": "process_sealed_holdout", "item_id": item_id}, self.registry)
        self.assertEqual(len(ids), 4)

    def test_historical_dataset_hash_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProtectedInputError, "protected dataset"):
            assert_not_protected({
                "split": "process_sealed_holdout",
                "source_dataset_sha256": "e2c8d0cf0838c3188fb1e1a98d27d633b8e551c577f3b7d7bb5d39090d7ad193",
            }, self.registry)

    def test_historical_provenance_is_rejected(self) -> None:
        with self.assertRaisesRegex(ProtectedInputError, "protected provenance"):
            assert_not_protected({
                "split": "process_sealed_holdout",
                "provenance_path": "/home/inspur/aic_video_work/temporal_round5/data/holdout.jsonl",
            }, self.registry)

    def test_nonprotected_dev_is_not_misclassified(self) -> None:
        assert_not_protected({"split": "dev", "item_id": "synthetic:dev:1"}, self.registry)

    def test_public_commitment_rejects_reference_payload(self) -> None:
        for key in ("reference_boxes", "trajectory", "item_iou", "best_reference"):
            with self.subTest(key=key), self.assertRaises(ProtectedInputError):
                assert_reference_payload_absent({key: []})


if __name__ == "__main__":
    unittest.main()
