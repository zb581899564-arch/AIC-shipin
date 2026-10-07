#!/usr/bin/env python3
"""Synthetic CPU all-empty/mixed frame, clock, composition and ZIP contracts."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch
import zipfile

try:
    from . import frame_contract as frames
    from . import package_contract as packages
except ImportError:
    import frame_contract as frames
    import package_contract as packages

HERE = Path(__file__).resolve().parent


def _fixture_builder():
    """Reuse only the old metadata fixture, never its model/media/runtime."""
    source = HERE.parent / "baseline_a_pts_v1" / "test_helpers.py"
    spec = importlib.util.spec_from_file_location("_next_round_synthetic_clock_fixture", source)
    module = importlib.util.module_from_spec(spec)
    old = {name: sys.modules.get(name) for name in ("a_contract", "pts_contract")}
    sys.modules["a_contract"], sys.modules["pts_contract"] = packages, frames
    try:
        spec.loader.exec_module(module)
    finally:
        for name, value in old.items():
            if value is None:
                sys.modules.pop(name, None)
            else:
                sys.modules[name] = value
    return module.make_fixture


make_fixture = _fixture_builder()


def temporal_for(manifest, clocks, positive_ids=()):
    rows = []
    for metadata in manifest["records"]:
        video_id = metadata["video_id"]
        windows = []
        for start, end in frames.window_schedule(metadata, manifest["kind"], clocks[video_id]):
            positive = video_id in positive_ids
            window = {"start_sec": start, "end_sec": end, "output_valid": True,
                      "status": "MODEL_OK" if positive else "LEGAL_EMPTY", "parse_errors": [],
                      "parse_warnings": [], "parsed_segments": [[0, min(0.3, end-start)]] if positive else []}
            if clocks[video_id]["branch"] == frames.BRANCH_NATIVE:
                window["clock_record_sha256"] = clocks[video_id]["clock_record_sha256"]
            windows.append(window)
        rows.append({"video_id": video_id, "n_frames": metadata["n_frames"],
                     "targetRatioWH": metadata["targetRatioWH"], "video_path": metadata["source_path"],
                     "fps": metadata["fps_num"] / metadata["fps_den"], "windows": windows})
    return rows


def spatial_for(selected):
    shots, previous = [], None
    for row in selected:
        key = (row["video_id"], row["source_frame"])
        start = previous is None or key[0] != previous[0] or key[1] != previous[1] + 1
        shots.append({**row, "is_shot_start": start})
        previous = key
    requests, outputs = [], []
    for shot in packages.group_shots(shots):
        by_frame = {row["source_frame"]: row for row in shot}
        for source_frame in packages.anchor_frames(list(by_frame), 8):
            row = by_frame[source_frame]
            request = {**row, "anchor_request_sha256": "a" * 64, "expected_pixel_sha256": "b" * 64}
            requests.append(request)
            outputs.append({"video_id": row["video_id"], "source_frame": source_frame,
                            "status": "MODEL_OK", "used_fallback": False,
                            "spatial_source": "QWEN_ANCHOR_SAME_FRAME", "anchor_request_sha256": "a" * 64,
                            "decoded_pixel_sha256": "b" * 64, "box_xyw": [0, 0, 36]})
    return shots, requests, outputs


class EmptyPipelineTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory(prefix="cpu_empty_fixture_", dir=HERE)
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def fixture(self, native_ids=(), kind="NONTEST_FROZEN8"):
        manifest, registry, path = make_fixture(self.root, native_ids=native_ids, kind=kind)
        clocks = frames.load_clocks(manifest, path, packages.sha(path))
        return manifest, clocks, registry, path

    def assert_all_empty_compose(self, manifest, selected):
        self.assertEqual(selected, [])
        self.assertEqual(packages.group_shots([]), [])
        predictions, provenance = packages.compose(frames.legacy_manifest(manifest), [], [], [], [])
        self.assertEqual(len(predictions), manifest["expected_count"])
        self.assertEqual({row["video_id"] for row in predictions}, {row["video_id"] for row in manifest["records"]})
        self.assertTrue(all(row["predictions"] == [] for row in predictions))
        self.assertEqual(provenance, [])
        report = packages.validate_predictions(frames.legacy_manifest(manifest), predictions, set(), provenance)
        self.assertTrue(report["legal_empty_supported"])
        self.assertEqual(report["prediction_frames"], 0)
        return predictions

    def test_cfr_all_empty_preserves_every_video_and_zero_spatial_requests(self):
        manifest, clocks, _, _ = self.fixture()
        selected = frames.select_frames(manifest, temporal_for(manifest, clocks), clocks)
        self.assert_all_empty_compose(manifest, selected)

    def test_native_all_empty_checks_clock_without_mapping_empty_segments(self):
        manifest, clocks, _, _ = self.fixture(native_ids=[str(i) for i in range(8)])
        with patch.object(frames, "native_segment_frames", side_effect=AssertionError("empty must skip mapping")) as mapping:
            selected = frames.select_frames(manifest, temporal_for(manifest, clocks), clocks)
        mapping.assert_not_called()
        self.assert_all_empty_compose(manifest, selected)

    def test_rematch426_all_empty_zip_crc_roundtrip_and_denominator(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0", "425"), kind="REMATCH426")
        predictions = self.assert_all_empty_compose(
            manifest, frames.select_frames(manifest, temporal_for(manifest, clocks), clocks))
        source, archive = self.root / "predictions.jsonl", self.root / "candidate_empty_synthetic.zip"
        packages.write_rows(source, predictions)
        receipt = packages.package(source, archive)
        self.assertFalse(receipt["uploaded"])
        with zipfile.ZipFile(archive) as zipped:
            self.assertEqual(zipped.namelist(), ["predictions.jsonl"])
            self.assertIsNone(zipped.testzip())
            recovered = [json.loads(line) for line in zipped.read("predictions.jsonl").decode("utf-8").splitlines()]
        self.assertEqual(recovered, predictions)
        self.assertEqual(len(recovered), 426)

    def test_mixed_empty_nonempty_cfr_native_composition_keeps_all_videos(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0", "7"))
        selected = frames.select_frames(manifest, temporal_for(manifest, clocks, {"0", "1"}), clocks)
        self.assertEqual({row["video_id"] for row in selected}, {"0", "1"})
        shots, requests, outputs = spatial_for(selected)
        predictions, provenance = packages.compose(frames.legacy_manifest(manifest), selected, shots, requests, outputs)
        self.assertEqual(len(predictions), 8)
        by_id = {row["video_id"]: row for row in predictions}
        self.assertTrue(by_id["0"]["predictions"])
        self.assertTrue(by_id["1"]["predictions"])
        self.assertTrue(all(by_id[str(i)]["predictions"] == [] for i in range(2, 8)))
        self.assertEqual(len(provenance), len(selected))
        self.assertEqual(packages.keyset(provenance), packages.keyset(selected))

    def test_failed_window_and_inconsistent_empty_status_cannot_turn_into_empty(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0",))
        valid = temporal_for(manifest, clocks)
        for mutation in ({"status": "PARSE_FAILURE"}, {"status": "INFERENCE_FAILURE"},
                         {"output_valid": False}, {"parse_errors": ["malformed"]},
                         {"parsed_segments": None}, {"status": "MODEL_OK"},
                         {"status": "LEGAL_EMPTY", "parsed_segments": [[0, 0.3]]}):
            with self.subTest(mutation=mutation):
                temporal = copy.deepcopy(valid)
                temporal[0]["windows"][0].update(mutation)
                with self.assertRaises(ValueError):
                    frames.select_frames(manifest, temporal, clocks)

    def test_cfr_failed_window_also_blocks_all_empty_fast_path(self):
        manifest, clocks, _, _ = self.fixture()
        temporal = temporal_for(manifest, clocks)
        temporal[0]["windows"][0]["status"] = "PARSE_FAILURE"
        with self.assertRaisesRegex(ValueError, "TEMPORAL_FAILURE"):
            frames.select_frames(manifest, temporal, clocks)

    def test_native_empty_still_rejects_changed_clock_hash(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0",))
        temporal = temporal_for(manifest, clocks)
        temporal[0]["windows"][0]["clock_record_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "CLOCK_EVIDENCE"):
            frames.select_frames(manifest, temporal, clocks)

    def test_native_empty_still_rejects_clock_array_byte_mismatch(self):
        manifest, _, registry, path = self.fixture(native_ids=("0",))
        array_path = Path(registry["records"][0]["clock_arrays"]["path"])
        array_path.write_text("{}\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "CLOCK_ARRAY_SHA_MISMATCH"):
            frames.load_clocks(manifest, path, packages.sha(path))

    def test_empty_does_not_bypass_clock_source_scope_or_window_coverage(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0",))
        temporal = temporal_for(manifest, clocks)
        with self.assertRaisesRegex(ValueError, "CLOCK_SET"):
            frames.select_frames(manifest, temporal, {})
        for key, value in (("video_path", "/synthetic_media/another.mp4"), ("n_frames", 100),
                           ("fps", 31), ("targetRatioWH", [16, 9])):
            corrupted = copy.deepcopy(temporal)
            corrupted[0][key] = value
            with self.assertRaises(ValueError):
                frames.select_frames(manifest, corrupted, clocks)
        for mutation in ("missing_window", "changed_window"):
            corrupted = copy.deepcopy(temporal)
            if mutation == "missing_window":
                corrupted[0]["windows"] = []
            else:
                corrupted[0]["windows"][0]["end_sec"] += 1
            with self.assertRaises(ValueError):
                frames.select_frames(manifest, corrupted, clocks)

    def test_positive_segment_with_no_native_frame_is_failure_not_empty(self):
        manifest, clocks, _, _ = self.fixture(native_ids=("0",))
        temporal = temporal_for(manifest, clocks)
        temporal[0]["windows"][0].update(status="MODEL_OK", parsed_segments=[[0.0001, 0.0002]])
        with self.assertRaisesRegex(ValueError, "NO_NATIVE_SOURCE_FRAMES"):
            frames.select_frames(manifest, temporal, clocks)

    def test_positive_segment_with_no_cfr_frame_is_failure_not_empty(self):
        manifest, clocks, _, _ = self.fixture()
        temporal = temporal_for(manifest, clocks)
        temporal[0]["windows"][0].update(status="MODEL_OK", parsed_segments=[[0.0001, 0.0002]])
        with self.assertRaisesRegex(ValueError, "no legal mapped frames"):
            frames.select_frames(manifest, temporal, clocks)

    def test_native_parser_has_no_rounding_or_endpoint_recovery(self):
        self.assertEqual(frames.parse_native_segments('{"segments":[]}', 2.3666666666666667), ([], [], [], []))
        parsed, errors, warnings, events = frames.parse_native_segments(
            '{"segments":[[0,2.3667]]}', 2.3666666666666667)
        self.assertIsNone(parsed)
        self.assertTrue(errors)
        self.assertEqual(warnings, [])
        self.assertEqual(events, [])

    def test_empty_official_rows_still_require_all_ids_and_selected_coverage(self):
        manifest, clocks, _, _ = self.fixture()
        predictions = self.assert_all_empty_compose(
            manifest, frames.select_frames(manifest, temporal_for(manifest, clocks), clocks))
        projected = frames.legacy_manifest(manifest)
        with self.assertRaises(ValueError):
            packages.validate_predictions(projected, predictions[:-1], set(), [])
        with self.assertRaises(ValueError):
            packages.validate_predictions(projected, predictions, {("0", 0)}, [])


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        raise FileExistsError("preserve CPU empty-pipeline evidence")
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(EmptyPipelineTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {"schema": "aic_next_round_empty_pipeline_cpu_v1", "status": "PASS" if result.wasSuccessful() else "FAIL",
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "output": stream.getvalue(), "source_sha256": {
                   name: hashlib.sha256((HERE / name).read_bytes()).hexdigest()
                   for name in ("package_contract.py", "frame_contract.py", "test_empty_pipeline.py")},
               "fixture_only": True, "model_run": False, "GPU_used": False,
               "contest_media_read": False, "semantic_labels_read": False, "quality_claim": False}
    if args.output is not None:
        args.output.parent.mkdir(parents=True, exist_ok=True)
        with args.output.open("x", encoding="utf-8") as target:
            json.dump(receipt, target, ensure_ascii=False, indent=2)
            target.write("\n")
    print(stream.getvalue())
    print(json.dumps({key: value for key, value in receipt.items() if key != "output"}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
