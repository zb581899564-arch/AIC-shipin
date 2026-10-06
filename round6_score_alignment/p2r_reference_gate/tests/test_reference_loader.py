import hashlib
import json
import math
import tempfile
import unittest
from pathlib import Path

from round6_score_alignment.p2r_reference_gate.reference_loader import (
    ReferenceValidationError,
    load_jsonl,
    sha256_file,
    validate_item,
    validate_manifest,
)
from round6_score_alignment.p2r_reference_gate.diagnostic_scoring import score_one_frame


class LoaderTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self.root = Path(self.tmp.name)
        (self.root / "a.bin").write_bytes(b"abc")
        self.item = {
            "dataset": "x", "item_id": "i", "source_group": "g", "split": "dev",
            "target_ratio_wh": [16, 9], "media_rel_path": "a.bin",
            "media_sha256": sha256_file(self.root / "a.bin"), "source_width": 160,
            "source_height": 90, "reference_boxes": [[0, 0, 160, 90]],
            "annotation_semantics": "human crop", "coverage": "single_image",
            "evidence_tier": "TIER_B_PUBLIC_ANNOTATION_LIMITED",
        }

    def tearDown(self): self.tmp.cleanup()

    def invalid(self, mutate):
        item = json.loads(json.dumps(self.item)); mutate(item)
        with self.assertRaises(ReferenceValidationError): validate_item(item, self.root)

    def test_valid(self): validate_item(self.item, self.root)
    def test_multi_reference_valid(self):
        self.item["reference_boxes"].append([0, 0, 160, 90]); validate_item(self.item, self.root)
    def test_missing_field(self): self.invalid(lambda x: x.pop("coverage"))
    def test_bool_coordinate(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[False, 0, 160, 90]]))
    def test_nan(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[0, 0, math.nan, 90]]))
    def test_inf(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[0, 0, math.inf, 90]]))
    def test_out_of_bounds(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[1, 0, 160, 90]]))
    def test_zero_area(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[0, 0, 0, 90]]))
    def test_wrong_ratio(self): self.invalid(lambda x: x.__setitem__("reference_boxes", [[0, 0, 90, 90]]))
    def test_missing_media(self): self.invalid(lambda x: x.__setitem__("media_rel_path", "missing"))
    def test_hash_mismatch(self): self.invalid(lambda x: x.__setitem__("media_sha256", "0" * 64))
    def test_empty_reference_rejected(self): self.invalid(lambda x: x.__setitem__("reference_boxes", []))
    def test_bad_split(self): self.invalid(lambda x: x.__setitem__("split", "test"))
    def test_sparse_allowed(self): self.item["coverage"] = "sparse"; validate_item(self.item, self.root)
    def test_duplicate_rejected(self):
        result = validate_manifest([self.item, self.item], self.root); self.assertEqual(result["status"], "INVALID_INPUT")
    def test_duplicate_frame_rejected(self):
        a = json.loads(json.dumps(self.item)); a["frame_index"] = 7
        b = json.loads(json.dumps(a)); b["item_id"] = "other"
        self.assertEqual(validate_manifest([a, b], self.root)["status"], "INVALID_INPUT")
    def test_source_leakage_rejected(self):
        b = json.loads(json.dumps(self.item)); b["item_id"] = "j"; b["split"] = "sealed_holdout"
        result = validate_manifest([self.item, b], self.root); self.assertEqual(result["status"], "INVALID_INPUT")
    def test_distinct_groups_pass(self):
        b = json.loads(json.dumps(self.item)); b["item_id"] = "j"; b["source_group"] = "h"; b["split"] = "sealed_holdout"
        self.assertEqual(validate_manifest([self.item, b], self.root)["status"], "OK")
    def test_invalid_jsonl(self):
        p = self.root / "x.jsonl"; p.write_text("{bad}\n", encoding="utf-8")
        with self.assertRaises(ReferenceValidationError): load_jsonl(p)
    def test_nonobject_jsonl(self):
        p = self.root / "x.jsonl"; p.write_text("[]\n", encoding="utf-8")
        with self.assertRaises(ReferenceValidationError): load_jsonl(p)
    def test_portrait_ratio_valid(self):
        self.item["target_ratio_wh"] = [9, 16]
        self.item["source_width"] = 90; self.item["source_height"] = 160
        self.item["reference_boxes"] = [[0, 0, 90, 160]]
        validate_item(self.item, self.root)
    def test_double_empty(self): self.assertEqual(score_one_frame([], []), 1.0)
    def test_prediction_only(self): self.assertEqual(score_one_frame([[0,0,1,1]], []), 0.0)
    def test_reference_only(self): self.assertEqual(score_one_frame([], [[0,0,1,1]]), 0.0)
    def test_multi_reference_best(self):
        self.assertEqual(score_one_frame([[0,0,2,2]], [[10,10,2,2],[0,0,2,2]]), 1.0)


if __name__ == "__main__": unittest.main()
