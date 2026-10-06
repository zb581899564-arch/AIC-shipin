"""P1a-fix regression tests.

Every test in this module was written *before* the fix and reproduced a
supervisor-confirmed defect (see reports/round6_score_alignment/SUPERVISOR_P1A_REVIEW.md).
They are kept as the regression suite for the fixed behaviour.

Defects covered
---------------
B1  ``load_reference`` treated a missing/null ``frames`` field as "no annotations"
    (``record.get("frames") or []``), so a single-video full reference of
    ``{"video_id": "0"}`` combined with an empty legal prediction scored OK/100.
B2  ``load_reference`` silently overwrote a duplicate ``video_id``
    (last-write-wins), so a duplicated id with empty frames also scored OK/100.
B3  the sparse branch returned full-video semantics
    (precision/recall/f1/time_f1, unmatched_predictions, both_empty, ...) even
    though unannotated frames are not negatives.
B4  ``SOURCE_SHOT_INTERPOLATION`` was a nearest-box copy, not interpolation.
B5  the traceable composition had no explicit failure/deliverability status.
B6  the declared distance limit accepted NaN/Infinity/float/bool values.
"""
from __future__ import annotations

import json
import subprocess
import sys
import tempfile
import unittest
from pathlib import Path

HERE = Path(__file__).resolve().parents[1]
if str(HERE) not in sys.path:
    sys.path.insert(0, str(HERE))
sys.dont_write_bytecode = True

from aic6 import scoring  # noqa: E402
from aic6.compose import (  # noqa: E402
    CompositionError,
    CompositionMode,
    ShotMap,
    WindowRequest,
    compose,
)
from aic6.segments import SegmentConstraint  # noqa: E402
from tests.hand_cases import BOX_FULL, two_video_index, write_predictions  # noqa: E402

try:  # imported lazily so the pre-fix run reports real defects, not one import error
    from aic6.cli import main as cli_main  # noqa: E402
except ImportError:  # pragma: no cover - only true before the fix
    cli_main = None


def require_cli():
    if cli_main is None:
        raise AssertionError("aic6.cli is missing: no public failure boundary exists")
    return cli_main


INDEX = two_video_index()
BANNED_SPARSE_KEYS = {
    "precision", "recall", "f1", "time_precision", "time_recall", "time_f1",
    "unmatched_predictions", "missed_ground_truth", "both_empty", "one_side_empty",
    "n_pred", "n_gt", "score_percent",
}


class ReferenceLoadingRegressionTests(unittest.TestCase):
    """B1/B2: a malformed or incomplete reference must never produce an OK score."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aic6_fix_")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def write_reference(self, payload) -> Path:
        path = self.tmp / "reference.json"
        path.write_text(json.dumps(payload), encoding="utf-8")
        return path

    def score_with(self, reference_path: Path) -> dict:
        predictions = write_predictions(self.tmp / "predictions.jsonl", {"0": [], "1": []})
        prediction_set = scoring.load_predictions(predictions, INDEX)
        reference = scoring.load_reference(reference_path, INDEX)
        return scoring.score_joint(predictions=prediction_set, reference=reference, index=INDEX)

    def test_missing_frames_field_is_rejected(self):
        # B1 reproduction: single video, legal empty prediction, reference record
        # {"video_id": "0"} only -> before the fix this produced OK / 100.0.
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                   "videos": [{"video_id": "0"}, {"video_id": "1", "frames": []}]}
        path = self.write_reference(payload)
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(path, INDEX)

    def test_null_frames_field_is_rejected(self):
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                   "videos": [{"video_id": "0", "frames": None}, {"video_id": "1", "frames": []}]}
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(self.write_reference(payload), INDEX)

    def test_non_list_frames_is_rejected(self):
        for bad in ({"5": BOX_FULL}, "frames", 5):
            payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                       "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                       "videos": [{"video_id": "0", "frames": bad},
                                  {"video_id": "1", "frames": []}]}
            with self.assertRaises(scoring.ReferenceError, msg=repr(bad)):
                scoring.load_reference(self.write_reference(payload), INDEX)

    def test_missing_or_null_videos_list_is_rejected(self):
        for videos in (None, {}, "x", 5):
            payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                       "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                       "videos": videos}
            with self.assertRaises(scoring.ReferenceError, msg=repr(videos)):
                scoring.load_reference(self.write_reference(payload), INDEX)
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic"}
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(self.write_reference(payload), INDEX)

    def test_duplicate_video_id_is_rejected_not_silently_overwritten(self):
        # B2 reproduction: first declares frame 0, the duplicate declares empty frames.
        # Before the fix the duplicate won and the case scored OK / 100.0.
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                   "videos": [{"video_id": "0", "frames": [{"frame": 0, "box_xyw": BOX_FULL}]},
                              {"video_id": "0", "frames": []},
                              {"video_id": "1", "frames": []}]}
        with self.assertRaises(scoring.ReferenceError):
            scoring.load_reference(self.write_reference(payload), INDEX)

    def test_explicit_empty_frames_list_is_still_allowed(self):
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                   "videos": [{"video_id": "0", "frames": []}, {"video_id": "1", "frames": []}]}
        reference = scoring.load_reference(self.write_reference(payload), INDEX)
        self.assertEqual(reference.video_ids(), {"0", "1"})
        self.assertEqual(sum(len(v) for v in reference.videos.values()), 0)

    def test_missing_provenance_metadata_is_rejected(self):
        for missing in ("label_status", "annotation_source"):
            payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                       "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                       "videos": [{"video_id": "0", "frames": []}, {"video_id": "1", "frames": []}]}
            payload.pop(missing)
            with self.assertRaises(scoring.ReferenceError, msg=missing):
                scoring.load_reference(self.write_reference(payload), INDEX)

    def test_reference_never_claims_trusted_annotation(self):
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "WEAK_TEACHER", "annotation_source": "weak labels",
                   "videos": [{"video_id": "0", "frames": []}, {"video_id": "1", "frames": []}]}
        reference = scoring.load_reference(self.write_reference(payload), INDEX)
        summary = reference.as_summary()
        self.assertFalse(summary["trusted_annotation"])
        self.assertEqual(summary["official_status"], "NOT_OFFICIAL_GROUND_TRUTH")

    def test_invalid_reference_cannot_produce_an_ok_score_via_the_public_boundary(self):
        payload = {"schema": "aic_round6_reference_v1", "coverage": "full",
                   "label_status": "SYNTHETIC", "annotation_source": "synthetic",
                   "videos": [{"video_id": "0"}, {"video_id": "1", "frames": []}]}
        reference_path = self.write_reference(payload)
        predictions = write_predictions(self.tmp / "predictions.jsonl", {"0": [], "1": []})
        index_path = self.tmp / "index.json"
        index_path.write_text(json.dumps({"records": [
            {"video_id": "0", "targetRatioWH": [16, 9], "width": 720, "height": 1280, "n_frames": 630},
            {"video_id": "1", "targetRatioWH": [16, 9], "width": 720, "height": 1280, "n_frames": 630},
        ]}), encoding="utf-8")
        out_path = self.tmp / "score.json"
        code = require_cli()(["score", "--predictions", str(predictions), "--reference",
                         str(reference_path), "--index", str(index_path), "--out", str(out_path)])
        self.assertNotEqual(code, 0)
        result = json.loads(out_path.read_text(encoding="utf-8"))
        self.assertIsNone(result["score"])
        self.assertEqual(result["status"], "INVALID_REFERENCE")
        self.assertNotEqual(result.get("status"), "OK")


class SparseDiagnosticRegressionTests(unittest.TestCase):
    """B3: sparse annotations must not be turned into full-video semantics."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aic6_fix_sparse_")
        self.tmp = Path(self._tmp.name)

    def tearDown(self):
        self._tmp.cleanup()

    def run_sparse(self, *, predictions, annotated):
        pred_path = write_predictions(self.tmp / "p.jsonl", predictions)
        ref_path = self.tmp / "r.json"
        ref_path.write_text(json.dumps({
            "schema": "aic_round6_reference_v1", "coverage": "sparse",
            "label_status": "WEAK_HUMAN_SPARSE", "annotation_source": "sparse keyframes",
            "videos": [{"video_id": "0", "coverage": "sparse", "frames": [
                {"frame": f, "box_xyw": list(b)} for f, b in sorted(annotated.items())]},
                {"video_id": "1", "coverage": "sparse", "frames": []}],
        }), encoding="utf-8")
        prediction_set = scoring.load_predictions(pred_path, INDEX)
        reference = scoring.load_reference(ref_path, INDEX)
        return scoring.score_joint(predictions=prediction_set, reference=reference, index=INDEX)

    def test_sparse_output_exposes_no_full_video_semantics(self):
        out = self.run_sparse(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                              annotated={5: BOX_FULL})
        self.assertEqual(out["status"], "SPARSE_DIAGNOSTIC")
        self.assertIsNone(out["score"])
        leaked = set()
        for row in out["per_video"]:
            leaked |= (set(row) & BANNED_SPARSE_KEYS)
        self.assertEqual(leaked, set(), msg=f"full-video semantics leaked: {sorted(leaked)}")
        self.assertNotIn("empty_both_count", out)
        self.assertNotIn("one_side_empty_count", out)

    def test_unannotated_predicted_frames_are_not_false_positives(self):
        # predictions on frames 5 and 6, only frame 5 annotated -> frame 6 is unverifiable,
        # so it must not appear as a false positive anywhere.
        out = self.run_sparse(predictions={"0": [{"frame": 5, "box": BOX_FULL},
                                                 {"frame": 6, "box": BOX_FULL}], "1": []},
                              annotated={5: BOX_FULL})
        row = [r for r in out["per_video"] if r["video_id"] == "0"][0]
        self.assertEqual(row["annotated_frames"], 1)
        self.assertEqual(row["matched_annotated_frames"], 1)
        self.assertEqual(row["predictions_not_evaluated"], 1)
        self.assertNotIn("unmatched_predictions", row)
        self.assertNotIn("f1", row)

    def test_missed_annotation_is_reported_without_precision_claim(self):
        out = self.run_sparse(predictions={"0": [], "1": []}, annotated={5: BOX_FULL})
        row = [r for r in out["per_video"] if r["video_id"] == "0"][0]
        self.assertEqual(row["annotated_frames"], 1)
        self.assertEqual(row["matched_annotated_frames"], 0)
        self.assertEqual(row["missed_annotated_frames"], 1)
        self.assertIsNone(row["mean_matched_iou_on_annotated_frames"])

    def test_zero_annotated_frames_is_no_evidence(self):
        out = self.run_sparse(predictions={"0": [{"frame": 5, "box": BOX_FULL}], "1": []},
                              annotated={})
        self.assertEqual(out["status"], "SPARSE_DIAGNOSTIC")
        self.assertIsNone(out["score"])
        self.assertEqual(out["sparse"]["evidence_status"], "NO_EVIDENCE")
        self.assertEqual(out["sparse"]["annotated_frames"], 0)
        self.assertNotIn("mean_matched_iou_on_annotated_frames_all",
                         {k: None for k in out["sparse"]})


class ShotNearestRegressionTests(unittest.TestCase):
    """B4/B6: accurate naming and a validated distance limit."""

    FPS = {"0": 30.0}
    N_FRAMES = {"0": 600}
    BOX = [0, 0, 720]
    SPATIAL = {"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}}
    SHOTS = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 600))})
    CONSTRAINT = SegmentConstraint(0, 5)
    RAW = '{"segments":[[0.0,0.2],[0.2,0.4],[10.0,10.2]]}'

    def compose_traceable(self, **kwargs):
        return compose(requests=[WindowRequest(video_id="0", index=0, start_sec=0.0,
                                               end_sec=11.0, raw_output=self.RAW)],
                       spatial_source=self.SPATIAL, fps_by_video=self.FPS,
                       n_frames_by_video=self.N_FRAMES, constraint=self.CONSTRAINT,
                       mode=CompositionMode.TRACEABLE,
                       shot_map=kwargs.pop("shot_map", self.SHOTS), **kwargs)

    def test_provenance_name_is_shot_nearest(self):
        report = self.compose_traceable(max_shot_nearest_gap_frames=10)
        blob = json.dumps(report, ensure_ascii=False)
        self.assertIn("SOURCE_SHOT_NEAREST", blob)
        self.assertNotIn("SOURCE_SHOT_INTERPOLATION", blob)
        self.assertIn("shot_nearest", report["totals"])
        self.assertNotIn("shot_interpolation", report["totals"])

    def test_no_linear_interpolation_claim_in_text_fields(self):
        report = self.compose_traceable(max_shot_nearest_gap_frames=10)
        blob = json.dumps(report, ensure_ascii=False).lower()
        self.assertNotIn("interpolat", blob)

    def test_distance_limit_must_be_a_finite_positive_integer(self):
        for bad in (float("nan"), float("inf"), float("-inf"), 0, -1, True, False, 1.5, "30", None):
            with self.assertRaises(CompositionError, msg=repr(bad)):
                self.compose_traceable(max_shot_nearest_gap_frames=bad)


class CompositionStatusRegressionTests(unittest.TestCase):
    """B5: the traceable mode needs an explicit failure/deliverability status."""

    FPS = {"0": 30.0}
    N_FRAMES = {"0": 600}
    BOX = [0, 0, 720]
    SPATIAL = {"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}}
    SHOTS = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 600))})
    CONSTRAINT = SegmentConstraint(0, 5)
    GOOD = '{"segments":[[0.0,0.2]]}'
    EMPTY = '{"segments":[]}'

    def run_windows(self, raws, spatial=None):
        requests = [WindowRequest(video_id="0", index=i, start_sec=float(i * 11),
                                  end_sec=float(i * 11 + 11), raw_output=raw)
                    for i, raw in enumerate(raws)]
        return compose(requests=requests, spatial_source=spatial or self.SPATIAL,
                       fps_by_video=self.FPS, n_frames_by_video=self.N_FRAMES,
                       constraint=self.CONSTRAINT, mode=CompositionMode.TRACEABLE,
                       shot_map=self.SHOTS, max_shot_nearest_gap_frames=10)

    def test_all_good_windows_are_deliverable(self):
        # window 0 selects frames 0..5, window 1 (start 11 s) selects frames 345..350;
        # a spatial source covering exactly those frames makes both windows resolvable.
        spatial = {"0": {f: self.BOX for f in list(range(0, 6)) + list(range(345, 351))}}
        report = self.run_windows([self.GOOD, '{"segments":[[0.5,0.7]]}'], spatial=spatial)
        self.assertEqual(report["status"], "OK_DELIVERABLE")
        self.assertTrue(report["deliverable"])
        self.assertEqual(report["totals"]["invalid_windows"], 0)
        self.assertEqual(report["totals"]["needs_spatial_inference"], 0)
        self.assertEqual(report["totals"]["same_frame"], 12)

    def test_one_bad_window_fails_the_whole_video(self):
        # a valid window followed by a parse failure must NOT be reported as success
        report = self.run_windows([self.GOOD, "not json at all"])
        self.assertEqual(report["status"], "FAILED_INVALID_WINDOWS")
        self.assertFalse(report["deliverable"])
        self.assertEqual(report["totals"]["invalid_windows"], 1)
        states = [w["state"] for w in report["videos"][0]["windows"]]
        self.assertIn("VALID_NONEMPTY", states)
        self.assertIn("INVALID", states)

    def test_legal_empty_only_is_still_a_success(self):
        report = self.run_windows([self.EMPTY])
        self.assertEqual(report["status"], "OK_DELIVERABLE")
        self.assertTrue(report["deliverable"])
        self.assertEqual(report["totals"]["empty_windows"], 1)
        self.assertEqual(report["totals"]["invalid_windows"], 0)

    def test_missing_spatial_source_is_not_deliverable(self):
        report = compose(requests=[WindowRequest(video_id="0", index=0, start_sec=10.0,
                                                 end_sec=21.0,
                                                 raw_output='{"segments":[[5.0,5.2]]}')],
                         spatial_source=self.SPATIAL, fps_by_video=self.FPS,
                         n_frames_by_video=self.N_FRAMES, constraint=self.CONSTRAINT,
                         mode=CompositionMode.TRACEABLE, shot_map=None)
        self.assertEqual(report["status"], "NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE")
        self.assertFalse(report["deliverable"])
        self.assertGreater(report["totals"]["needs_spatial_inference"], 0)

    def test_invalid_window_takes_precedence_over_missing_spatial(self):
        report = self.run_windows(["not json at all"])
        self.assertEqual(report["status"], "FAILED_INVALID_WINDOWS")

    def test_legacy_replay_is_never_a_delivery_path(self):
        report = compose(requests=[WindowRequest(video_id="0", index=0, start_sec=0.0,
                                                 end_sec=11.0, raw_output=self.GOOD)],
                         spatial_source=self.SPATIAL, fps_by_video=self.FPS,
                         n_frames_by_video=self.N_FRAMES, constraint=self.CONSTRAINT,
                         mode=CompositionMode.LEGACY_REPLAY, shot_map=None)
        self.assertEqual(report["status"], "LEGACY_REPLAY_COMPLETED")
        self.assertFalse(report["deliverable"])


class CliExitCodeTests(unittest.TestCase):
    """The public call boundary must fail loudly (non-zero exit)."""

    def setUp(self):
        self._tmp = tempfile.TemporaryDirectory(prefix="aic6_fix_cli_")
        self.tmp = Path(self._tmp.name)
        (self.tmp / "index.json").write_text(json.dumps({"records": [
            {"video_id": "0", "targetRatioWH": [16, 9], "width": 720, "height": 1280, "n_frames": 630},
            {"video_id": "1", "targetRatioWH": [16, 9], "width": 720, "height": 1280, "n_frames": 630},
        ]}), encoding="utf-8")

    def tearDown(self):
        self._tmp.cleanup()

    def test_score_cli_reports_not_computable_with_nonzero_exit(self):
        predictions = write_predictions(self.tmp / "p.jsonl", {"0": [], "1": []})
        out = self.tmp / "score.json"
        code = require_cli()(["score", "--predictions", str(predictions),
                         "--index", str(self.tmp / "index.json"), "--out", str(out)])
        self.assertNotEqual(code, 0)
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "NOT_COMPUTABLE")

    def test_score_cli_ok_path_exits_zero(self):
        predictions = write_predictions(self.tmp / "p.jsonl", {"0": [], "1": []})
        ref = self.tmp / "r.json"
        ref.write_text(json.dumps({
            "schema": "aic_round6_reference_v1", "coverage": "full",
            "label_status": "SYNTHETIC", "annotation_source": "synthetic",
            "videos": [{"video_id": "0", "frames": []}, {"video_id": "1", "frames": []}]}),
            encoding="utf-8")
        out = self.tmp / "score.json"
        code = require_cli()(["score", "--predictions", str(predictions), "--reference", str(ref),
                         "--index", str(self.tmp / "index.json"), "--out", str(out)])
        self.assertEqual(code, 0)
        result = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "OK")
        self.assertEqual(result["score"], 100.0)

    def test_compose_cli_exits_nonzero_when_not_deliverable(self):
        spatial = self.tmp / "spatial.jsonl"
        spatial.write_text(json.dumps({"video_id": "0", "targetRatioWH": [16, 9],
                                       "predictions": [{"frame": 0, "bboxes": [0, 0, 720]}]}) + "\n",
                           encoding="utf-8")
        temporal = self.tmp / "temporal.jsonl"
        temporal.write_text(json.dumps({
            "video_id": "0", "fps": 30.0, "n_frames": 600, "targetRatioWH": [16, 9],
            "windows": [{"index": 0, "start_sec": 0.0, "end_sec": 10.0,
                         "duration_sec": 10.0, "raw_output": '{"segments":[[5.0,5.5]]}'}]}) + "\n",
            encoding="utf-8")
        out = self.tmp / "compose.json"
        code = require_cli()(["compose", "--temporal", str(temporal), "--spatial", str(spatial),
                         "--out", str(out)])
        self.assertNotEqual(code, 0)
        result = json.loads(out.read_text(encoding="utf-8"))
        self.assertEqual(result["status"], "NOT_DELIVERABLE_NEEDS_SPATIAL_INFERENCE")
        self.assertFalse(result["deliverable"])

    def test_subprocess_boundary_returns_the_same_nonzero_code(self):
        predictions = write_predictions(self.tmp / "p.jsonl", {"0": [], "1": []})
        out = self.tmp / "score.json"
        require_cli()
        proc = subprocess.run(
            [sys.executable, "-B", "-m", "aic6.cli", "score", "--predictions", str(predictions),
             "--index", str(self.tmp / "index.json"), "--out", str(out)],
            cwd=str(HERE), capture_output=True, text=True)
        self.assertNotEqual(proc.returncode, 0, msg=proc.stderr[-500:])
        self.assertEqual(json.loads(out.read_text(encoding="utf-8"))["status"], "NOT_COMPUTABLE")


if __name__ == "__main__":
    unittest.main()
