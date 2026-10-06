from __future__ import annotations

import contextlib
import hashlib
import io
import json
import math
import os
import re
import sys
import tempfile
import unittest
from pathlib import Path

CODE_DIR = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(CODE_DIR))

import evaluate_process_sealed
from sealed_evaluator import sha256_file


class ProcessSealedTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls) -> None:
        run_dir = os.environ.get("P2R9_RUN_DIR")
        if not run_dir:
            raise RuntimeError("P2R9_RUN_DIR is required")
        cls.registry_source = Path(run_dir) / "protected_input_registry.json"
        cls.root = Path(__file__).resolve().parents[3]

    def setUp(self) -> None:
        self.tmp_context = tempfile.TemporaryDirectory()
        self.tmp = Path(self.tmp_context.name)
        self.registry = self.tmp / "protected_input_registry.json"
        self.registry.write_bytes(self.registry_source.read_bytes())
        self.reference = self.tmp / "private_reference.jsonl"
        self.predictions = self.tmp / "predictions.jsonl"
        self.commitment = self.tmp / "holdout_commitment.json"
        self.access_log = self.tmp / "holdout_access_log.jsonl"
        self.wrapper = CODE_DIR / "evaluate_process_sealed.py"
        self.engine = CODE_DIR / "sealed_evaluator.py"
        self.refs = [
            {
                "item_id": "synthetic:item:1", "source_group": "synthetic:group:1",
                "media_sha256": "1" * 64, "source_width": 180, "source_height": 160,
                "target_ratio_wh": [9, 16], "reference_boxes": [[0, 0, 90, 160], [45, 0, 90, 160]],
                "coverage": "sparse_frame",
            },
            {
                "item_id": "synthetic:item:2", "source_group": "synthetic:group:2",
                "media_sha256": "2" * 64, "source_width": 180, "source_height": 160,
                "target_ratio_wh": [9, 16], "reference_boxes": [], "coverage": "single_image",
            },
        ]
        self.preds = [
            {
                "item_id": "synthetic:item:1", "source_group": "synthetic:group:1",
                "media_sha256": "1" * 64, "target_ratio_wh": [9, 16], "status": "OK",
                "predicted_boxes": [[45, 0, 90, 160]],
            },
            {
                "item_id": "synthetic:item:2", "source_group": "synthetic:group:2",
                "media_sha256": "2" * 64, "target_ratio_wh": [9, 16], "status": "OK",
                "predicted_boxes": [],
            },
        ]
        self.write_jsonl(self.reference, self.refs)
        self.write_jsonl(self.predictions, self.preds)
        self.refresh_commitment()

    def tearDown(self) -> None:
        self.tmp_context.cleanup()

    @staticmethod
    def write_json(path: Path, value: object) -> None:
        path.write_text(json.dumps(value, ensure_ascii=False, allow_nan=True), encoding="utf-8")

    @staticmethod
    def write_jsonl(path: Path, rows: list[dict]) -> None:
        path.write_text("".join(json.dumps(row, ensure_ascii=False, allow_nan=True) + "\n" for row in rows), encoding="utf-8")

    def refresh_commitment(self, **overrides: object) -> dict:
        value = {
            "schema": "p2r9_holdout_commitment_v1",
            "status": "BOUND",
            "dataset_version": "SYNTHETIC_ONLY_v1",
            "source_dataset_sha256": "9" * 64,
            "selection_rule": "synthetic fixed fixture",
            "selection_seed": 20260920,
            "item_count": len(self.refs),
            "items": [
                {
                    "item_id": row["item_id"], "source_group": row["source_group"],
                    "media_sha256": row["media_sha256"], "target_ratio_wh": row["target_ratio_wh"],
                }
                for row in self.refs
            ],
            "dev_source_group_sha256": [],
            "reference_labels_sha256": sha256_file(self.reference),
            "evaluator_sha256": sha256_file(self.wrapper),
            "engine_sha256": sha256_file(self.engine),
            "protected_registry_sha256": sha256_file(self.registry),
        }
        value.update(overrides)
        self.write_json(self.commitment, value)
        return value

    def invoke(self) -> tuple[int, dict, str]:
        stdout = io.StringIO()
        args = [
            "--commitment", str(self.commitment),
            "--sealed-reference", str(self.reference),
            "--predictions", str(self.predictions),
            "--protected-registry", str(self.registry),
            "--access-log", str(self.access_log),
        ]
        with contextlib.redirect_stdout(stdout):
            code = evaluate_process_sealed.main(args)
        raw = stdout.getvalue()
        return code, json.loads(raw), raw

    def assert_refused(self, error_code: str) -> dict:
        code, result, raw = self.invoke()
        self.assertNotEqual(code, 0)
        self.assertEqual(result["status"], "REFUSED")
        self.assertEqual(result["error_code"], error_code)
        self.assertNotIn("reference_boxes", raw)
        self.assertNotIn("synthetic:item", raw)
        return result

    def test_valid_aggregate_and_multi_reference_best(self) -> None:
        code, result, raw = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result["status"], "PASS_AGGREGATE")
        self.assertEqual(result["macro_item_mean_iou"], 1.0)
        self.assertEqual(result["macro_source_group_mean_iou"], 1.0)
        self.assertEqual(result["empty_empty_items"], 1)
        self.assertEqual(result["sparse_items"], 1)
        for forbidden in ("reference_boxes", "predicted_boxes", "item_id", "best_reference", "per_item"):
            self.assertNotIn(forbidden, raw)

    def test_access_log_is_append_only_and_aggregate_only(self) -> None:
        self.invoke()
        first = self.access_log.read_bytes()
        self.invoke()
        second = self.access_log.read_bytes()
        self.assertTrue(second.startswith(first))
        rows = [json.loads(line) for line in second.decode().splitlines()]
        self.assertEqual(len(rows), 2)
        self.assertNotIn("reference_boxes", second.decode())
        self.assertNotIn("item_id", second.decode())

    def test_missing_prediction_fails(self) -> None:
        self.write_jsonl(self.predictions, self.preds[:1])
        self.assert_refused("MISSING_PREDICTION")

    def test_extra_prediction_fails(self) -> None:
        extra = dict(self.preds[0]); extra["item_id"] = "synthetic:extra"
        self.write_jsonl(self.predictions, self.preds + [extra])
        self.assert_refused("EXTRA_PREDICTION")

    def test_duplicate_prediction_fails(self) -> None:
        self.write_jsonl(self.predictions, self.preds + [self.preds[0]])
        self.assert_refused("DUPLICATE_PREDICTION")

    def test_invalid_json_fails_without_trace(self) -> None:
        self.predictions.write_text("{not-json}\n", encoding="utf-8")
        self.assert_refused("INVALID_PREDICTION_JSON")

    def test_nan_infinity_and_bool_fail(self) -> None:
        for value in (math.nan, math.inf, True):
            with self.subTest(value=value):
                rows = json.loads(json.dumps(self.preds))
                rows[0]["predicted_boxes"][0][0] = value
                self.write_jsonl(self.predictions, rows)
                self.assert_refused("INVALID_PREDICTION_JSON" if isinstance(value, float) and not math.isfinite(value) else "INVALID_PREDICTION_BOX")

    def test_out_of_bounds_fails(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["predicted_boxes"] = [[100, 0, 90, 160]]
        self.write_jsonl(self.predictions, rows)
        self.assert_refused("INVALID_PREDICTION_BOX")

    def test_wrong_ratio_fails(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["predicted_boxes"] = [[0, 0, 80, 160]]
        self.write_jsonl(self.predictions, rows)
        self.assert_refused("WRONG_BOX_RATIO")

    def test_media_hash_mismatch_fails(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["media_sha256"] = "0" * 64
        self.write_jsonl(self.predictions, rows)
        self.assert_refused("MEDIA_HASH_MISMATCH")

    def test_ratio_mismatch_fails(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["target_ratio_wh"] = [16, 9]
        self.write_jsonl(self.predictions, rows)
        self.assert_refused("RATIO_MISMATCH")

    def test_source_split_leakage_fails(self) -> None:
        blocked = hashlib.sha256("synthetic:group:1".encode()).hexdigest()
        self.refresh_commitment(dev_source_group_sha256=[blocked])
        self.assert_refused("SOURCE_SPLIT_LEAKAGE")

    def test_failed_prediction_remains_in_denominator(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["status"] = "FAILED"; rows[0]["predicted_boxes"] = []
        self.write_jsonl(self.predictions, rows)
        code, result, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result["failed_items"], 1)
        self.assertEqual(result["macro_item_mean_iou"], 0.5)

    def test_one_empty_scores_zero(self) -> None:
        rows = json.loads(json.dumps(self.preds)); rows[0]["predicted_boxes"] = []
        self.write_jsonl(self.predictions, rows)
        code, result, _ = self.invoke()
        self.assertEqual(code, 0)
        self.assertEqual(result["single_empty_items"], 1)
        self.assertEqual(result["macro_item_mean_iou"], 0.5)

    def test_reference_hash_change_fails(self) -> None:
        self.reference.write_bytes(self.reference.read_bytes() + b"\n")
        self.assert_refused("REFERENCE_HASH_MISMATCH")

    def test_code_hash_change_fails(self) -> None:
        self.refresh_commitment(evaluator_sha256="0" * 64)
        self.assert_refused("EVALUATOR_HASH_MISMATCH")

    def test_engine_hash_change_fails(self) -> None:
        self.refresh_commitment(engine_sha256="0" * 64)
        self.assert_refused("ENGINE_HASH_MISMATCH")

    def test_commitment_with_coordinates_is_refused(self) -> None:
        value = self.refresh_commitment(); value["reference_boxes"] = [[1, 2, 3, 4]]
        self.write_json(self.commitment, value)
        self.assert_refused("COMMITMENT_EXPOSES_REFERENCE")

    def test_unbound_commitment_is_refused(self) -> None:
        self.refresh_commitment(status="NOT_BOUND")
        self.assert_refused("COMMITMENT_NOT_BOUND")

    def test_old_weak_holdout_identity_component_is_refused(self) -> None:
        weak_path = self.root / "reports/round6_score_alignment/training_alignment_20260917/weak_split_manifest.jsonl"
        old = next(json.loads(line) for line in weak_path.read_text(encoding="utf-8").splitlines() if json.loads(line).get("split") == "holdout")
        self.refs[0]["video_id"] = old["video_id"]
        self.write_jsonl(self.reference, self.refs); self.refresh_commitment()
        self.assert_refused("PROTECTED_INPUT_REJECTED")

    def test_exposed_gnmc_item_id_is_refused(self) -> None:
        path = self.root / "reports/round6_score_alignment/p2r_reference_gate/round6_p2r_20260919T154701Z/sealed_holdout_manifest.jsonl"
        line = next(line for line in path.read_text(encoding="utf-8").splitlines() if line.strip())
        item_id = json.loads(re.search(r'"item_id"\s*:\s*("(?:[^"\\]|\\.)*")', line).group(1))
        self.refs[0]["item_id"] = item_id; self.preds[0]["item_id"] = item_id
        self.write_jsonl(self.reference, self.refs); self.write_jsonl(self.predictions, self.preds); self.refresh_commitment()
        self.assert_refused("PROTECTED_INPUT_REJECTED")

    def test_historical_dataset_hash_is_refused(self) -> None:
        self.refresh_commitment(source_dataset_sha256="e2c8d0cf0838c3188fb1e1a98d27d633b8e551c577f3b7d7bb5d39090d7ad193")
        self.assert_refused("PROTECTED_INPUT_REJECTED")

    def test_reference_payload_marker_never_leaks_on_exception(self) -> None:
        marker = "DO_NOT_LEAK_PRIVATE_REFERENCE_MARKER"
        self.refs[0]["reference_boxes"] = marker
        self.write_jsonl(self.reference, self.refs); self.refresh_commitment()
        _, _, raw = self.invoke()
        self.assertNotIn(marker, raw)
        self.assertNotIn("Traceback", raw)


if __name__ == "__main__":
    unittest.main()
