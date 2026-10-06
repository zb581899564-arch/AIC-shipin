#!/usr/bin/env python3
"""CPU numerical regressions only; no contest media, labels or models."""
from __future__ import annotations

import argparse
import copy
import io
import json
import subprocess
import sys
import tempfile
import unittest
from contextlib import redirect_stdout
from pathlib import Path
from unittest.mock import patch

sys.dont_write_bytecode = True
from a_contract import sha, write_json
from numeric_source_worker import parse_ffprobe
from scan_source_origin import audit_numeric, scan_records, verify_dependencies
from time_origin_core import audit_origin, probe_indices

HERE = Path(__file__).resolve().parent


def fixture(origin=0.046, n=942, fps_num=30, fps_den=1, clock="relative", quantize=False):
    fps = fps_num/fps_den
    raw = [origin+(round(i/fps, 3) if quantize else i/fps) for i in range(n)]
    starts = raw if clock == "raw" else [p-origin for p in raw]
    numeric = {"width": 640, "height": 360, "ffprobe_fps_num": fps_num, "ffprobe_fps_den": fps_den,
               "stream_time_base": "1/16000", "stream_start_time": origin,
               "stream_start_pts": round(origin*16000), "stream_start_pts_sec": origin,
               "raw_pts_sec": raw, "raw_integer_pts_count": n, "raw_textual_pts_count": n,
               "max_integer_text_pts_error_sec": 0.0, "decord_frames": n, "decord_fps": fps,
               "decord_numeric_epsilon": 2**-23, "decord_timestamp_dtype": "float32",
               "decord_timestamps": [[p, p+1/fps] for p in starts], "decord_version": "SYNTHETIC_NUMERICAL",
               "images_exported_or_displayed": False}
    row = {"video_id": "18", "source_sha256": "0"*64, "fps_num": fps_num, "fps_den": fps_den,
           "n_frames": n, "width": 640, "height": 360}
    return row, numeric


class OriginTests(unittest.TestCase):
    def audit(self, row, numeric):
        return audit_numeric(row, numeric)

    def failure(self, mutator, code):
        row, numeric = fixture()
        mutator(row, numeric)
        receipt = self.audit(row, numeric)
        self.assertFalse(receipt["pass"])
        self.assertIn(code, receipt["failures"])

    def test_nonzero_origin_relative_all_942(self):
        row, numeric = fixture(quantize=True)
        r = self.audit(row, numeric)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(r["decord_clock_mode"], "SOURCE_RELATIVE_PTS")
        self.assertTrue(r["decord_all_frame_binding_checked"])
        self.assertEqual(r["decord_all_frame_timestamp_count"], 942)
        self.assertAlmostEqual(r["max_normalized_cfr_error_sec"], 1/3000, places=10)
        self.assertEqual(r["one_frame_tolerance_sec"], 1/30+1e-6)
        self.assertFalse(abs(numeric["raw_pts_sec"][0]) <= r["one_frame_tolerance_sec"])

    def test_nonzero_origin_raw_clock(self):
        row, numeric = fixture(clock="raw")
        r = self.audit(row, numeric)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(r["decord_clock_mode"], "RAW_CONTAINER_PTS")

    def test_zero_origin(self):
        row, numeric = fixture(origin=0)
        r = self.audit(row, numeric)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(r["decord_clock_mode"], "RAW_AND_RELATIVE_EQUIVALENT_ZERO_ORIGIN")

    def test_fractional_fps_and_negative_origin(self):
        row, numeric = fixture(origin=-2, fps_num=30000, fps_den=1001)
        self.assertTrue(self.audit(row, numeric)["pass"])

    def test_large_raw_origin_does_not_inflate_relative_bound(self):
        row, numeric = fixture(origin=1000000)
        r = self.audit(row, numeric)
        self.assertTrue(r["pass"], r["failures"])
        self.assertEqual(r["decord_relative_binding_tolerance_sec"], 1/16000)
        numeric["decord_timestamps"][123][0] += 0.005
        self.assertFalse(self.audit(row, numeric)["pass"])

    def test_decoder_bad_non_probe_frame(self):
        self.assertNotIn(123, probe_indices(942))
        self.failure(lambda r, n: n["decord_timestamps"][123].__setitem__(0, n["decord_timestamps"][123][0]+0.002),
                     "DECORD_RAW_OR_SOURCE_RELATIVE_ORIGIN_BINDING_FAILED")

    def test_vfr_or_wrong_fps_drift_keeps_legacy_gate(self):
        row, numeric = fixture()
        for i in range(500, row["n_frames"]):
            numeric["raw_pts_sec"][i] += 0.04
            numeric["decord_timestamps"][i] = [x+0.04 for x in numeric["decord_timestamps"][i]]
        r = self.audit(row, numeric)
        self.assertIn("NORMALIZED_CFR_ERROR_EXCEEDS_UNCHANGED_ONE_FRAME_TOLERANCE", r["failures"])
        self.assertEqual(r["one_frame_tolerance_sec"], 1/30+1e-6)

    def test_legacy_one_frame_boundary_is_not_tightened(self):
        row, numeric = fixture()
        shift = 1/30
        for i in range(1, row["n_frames"]):
            numeric["raw_pts_sec"][i] += shift
            numeric["decord_timestamps"][i] = [x+shift for x in numeric["decord_timestamps"][i]]
        self.assertTrue(self.audit(row, numeric)["pass"])

    def test_raw_missing(self):
        self.failure(lambda r, n: n["raw_pts_sec"].__setitem__(17, None), "RAW_PTS_NONFINITE_OR_MISSING")

    def test_raw_nonfinite(self):
        self.failure(lambda r, n: n["raw_pts_sec"].__setitem__(17, float("nan")), "RAW_PTS_NONFINITE_OR_MISSING")

    def test_raw_duplicate(self):
        self.failure(lambda r, n: n["raw_pts_sec"].__setitem__(17, n["raw_pts_sec"][16]), "RAW_PTS_NOT_STRICTLY_MONOTONIC")

    def test_raw_wrong_count(self):
        self.failure(lambda r, n: n["raw_pts_sec"].pop(), "RAW_PTS_FRAME_COUNT_MISMATCH")

    def test_unknown_stream_start(self):
        self.failure(lambda r, n: n.__setitem__("stream_start_time", None), "STREAM_START_METADATA_UNCONFIRMED")

    def test_wrong_stream_start(self):
        self.failure(lambda r, n: n.__setitem__("stream_start_time", 0), "STREAM_START_AND_FIRST_PRESENTATION_PTS_ORIGINS_DISAGREE")

    def test_negative_timebase(self):
        self.failure(lambda r, n: n.__setitem__("stream_time_base", "-1/16000"), "STREAM_TIME_BASE_UNCONFIRMED")

    def test_decoder_wrong_count(self):
        self.failure(lambda r, n: n.__setitem__("decord_frames", 941), "DECORD_REGISTERED_COUNT_OR_FPS_MISMATCH")

    def test_decoder_missing_timestamp(self):
        self.failure(lambda r, n: n["decord_timestamps"].pop(), "DECORD_ALL_FRAME_TIMESTAMP_COUNT_MISMATCH")

    def test_decoder_nan(self):
        self.failure(lambda r, n: n["decord_timestamps"][17].__setitem__(0, float("nan")), "DECORD_TIMESTAMPS_INVALID")

    def test_decoder_bad_end(self):
        self.failure(lambda r, n: n["decord_timestamps"][17].__setitem__(1, 200), "DECORD_INTERVAL_END_OR_DURATION_INVALID")

    def test_decoder_unknown_precision(self):
        self.failure(lambda r, n: n.__setitem__("decord_numeric_epsilon", 1), "DECORD_FLOAT_REPRESENTATION_UNCONFIRMED")

    def test_integer_pts_missing_cannot_fallback_to_text(self):
        self.failure(lambda r, n: n.__setitem__("raw_integer_pts_count", 941), "ALL_INTEGER_AND_TEXTUAL_RAW_PTS_REQUIRED")

    def test_text_pts_missing_blocks(self):
        self.failure(lambda r, n: n.__setitem__("max_integer_text_pts_error_sec", None), "INTEGER_TIMEBASE_AND_TEXTUAL_PTS_DISAGREE_OR_MISSING")

    def test_integer_stream_start_missing(self):
        self.failure(lambda r, n: n.__setitem__("stream_start_pts_sec", None), "STREAM_INTEGER_AND_TEXTUAL_START_ORIGIN_UNCONFIRMED")

    def test_parser_integer_not_reconstructed_from_text(self):
        parsed = parse_ffprobe({"streams": [{"width": 640, "height": 360, "time_base": "1/16000",
                                            "avg_frame_rate": "30/1", "start_pts": 736, "start_time": "0.046000"}],
                                "frames": [{"best_effort_timestamp_time": "0.046000"}]})
        self.assertEqual(parsed["raw_pts_sec"], [None])
        self.assertEqual(parsed["raw_integer_pts_count"], 0)

    def test_dependency_and_production_hashes(self):
        self.assertEqual(len(verify_dependencies()), 3)

    def test_all_426_continue_after_native_failure_and_bad_timestamp(self):
        with tempfile.TemporaryDirectory(prefix="cpu_origin_fixture_", dir=HERE) as name:
            root = Path(name)
            source = root/"synthetic_bytes_not_media.bin"
            source.write_bytes(b"synthetic source identity fixture")
            row, numeric = fixture(n=12)
            records = []
            for i in range(426):
                records.append(dict(row, video_id=str(i), source_path=str(source), source_sha256=sha(source)))
            manifest = {"allowed_source_roots": [str(root)], "records": records}
            def worker(src, ffprobe, output, log, timeout, threads):
                vid = output.stem.split(".")[0]
                log.write_text("synthetic worker\n", encoding="utf-8")
                if vid == "3":
                    raise subprocess.CalledProcessError(-11, ["synthetic_worker"])
                payload = copy.deepcopy(numeric)
                if vid == "19":
                    payload["decord_timestamps"][4][0] += 0.01
                write_json(output, payload)
            with patch("scan_source_origin.run_numeric_worker", side_effect=worker), redirect_stdout(io.StringIO()):
                results, registry = scan_records(manifest, root, Path("synthetic_ffprobe"), 900, 0)
            self.assertEqual(len(results), 426)
            self.assertEqual(len(registry), 426)
            self.assertEqual([r["video_id"] for r in results if not r["pass"]], ["3", "19"])
            self.assertTrue(results[-1]["pass"])
            self.assertEqual(len(list((root/"records").glob("*.identity.json"))), 426)


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--output", type=Path, required=True)
    args = ap.parse_args()
    if args.output.exists():
        raise FileExistsError("preserve prior CPU regression receipt")
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(OriginTests)
    stream = io.StringIO()
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {"status": "PASS_CPU_NUMERICAL_ONLY" if result.wasSuccessful() else "FAIL_CPU_NUMERICAL",
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "output": stream.getvalue(), "contest_media_read": False, "labels_read": False,
               "GPU_used": False, "real_decoder_synthetic_media_verified": False,
               "source_code": verify_dependencies(), "test_file_sha256": sha(__file__)}
    write_json(args.output, receipt)
    print(stream.getvalue())
    print(json.dumps({k: v for k, v in receipt.items() if k != "output"}, ensure_ascii=False))
    return 0 if result.wasSuccessful() else 1


if __name__ == "__main__":
    raise SystemExit(main())
