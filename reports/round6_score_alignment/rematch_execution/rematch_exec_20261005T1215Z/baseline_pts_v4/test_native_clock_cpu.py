#!/usr/bin/env python3
"""CPU stdlib fixtures and bound existing failed-source numeric regressions."""
from __future__ import annotations

import ast
import copy
from fractions import Fraction
import json
from pathlib import Path
import tempfile
import unittest

from native_clock_core import audit_record, bind_float32, f32, reconstruct_integer_ticks
from registry_io import (PRODUCTION_FILES, REMATCH_SHA, V3_RECEIPT_SHA, read_bound, sha, verify_source_lock, write_bundle)

HERE = Path(__file__).parent
RUN = HERE.parent


def fixture(ticks=(0, 1, 2, 3), origin=0):
    tick = Fraction(1, 10)
    ticks = [v + origin for v in ticks]
    row = {"video_id": "fixture", "source_sha256": "a" * 64, "width": 20, "height": 20,
           "n_frames": len(ticks), "fps_num": 10, "fps_den": 1}
    numeric = {"raw_pts_sec": [float(p * tick) for p in ticks], "stream_time_base": str(tick),
        "stream_start_pts": ticks[0], "stream_start_pts_sec": float(ticks[0] * tick),
        "stream_start_time": float(ticks[0] * tick), "width": 20, "height": 20,
        "ffprobe_fps_num": 10, "ffprobe_fps_den": 1, "raw_integer_pts_count": len(ticks),
        "raw_textual_pts_count": len(ticks), "max_integer_text_pts_error_sec": 0.0,
        "decord_timestamp_dtype": "float32", "decord_numeric_epsilon": 2**-23,
        "decord_frames": len(ticks), "decord_fps": 10.0,
        "decord_timestamps": [[f32(p * tick), f32((p + 1) * tick)] for p in ticks],
        "automatic_all_frame_metadata_scan": True, "images_exported_or_displayed": False}
    prior = {"source_sha256": "a" * 64, "source_hash_verified_before_and_after": True,
             "media_rewritten": False, "pass": False, "failures": ["HISTORICAL_V3_FIXTURE"]}
    add = {"source_sha256": "a" * 64, "source_sha256_before": "a" * 64,
           "source_sha256_after": "a" * 64, "source_hash_verified_before_and_after": True}
    probe = {"streams": [{"width": 20, "height": 20, "time_base": str(tick), "avg_frame_rate": "10/1",
        "start_pts": ticks[0], "start_time": str(float(ticks[0] * tick)),
        "duration_ts": ticks[-1] - ticks[0], "duration": str(float((ticks[-1] - ticks[0]) * tick))}],
        "frames": [{"best_effort_timestamp": p, "best_effort_timestamp_time": str(float(p * tick)),
                    "pkt_duration": 1, "pkt_duration_time": "0.1"} for p in ticks]}
    return row, numeric, prior, add, probe


class NativeClockCpuTests(unittest.TestCase):
    def test_cfr_legacy_endpoint_not_falsely_native_packet(self):
        result, arrays = audit_record(*fixture()[:3])
        self.assertTrue(result["identity_pass"] and result["cfr_eligible"] and result["usable"])
        self.assertFalse(result["native_clock_usable"])
        self.assertEqual(result["duration_seconds"], 0.4)
        self.assertEqual(result["terminal_evidence"]["kind"], "LEGACY_CFR_N_DIV_FPS")
        self.assertTrue(result["decord_binding"]["legacy_interval_pass"])
        self.assertFalse(result["decord_binding"]["end_pass"])
        self.assertIsNone(arrays["native_frame_end_pts_ticks"])

    def test_native_packet_end_header_discrepancy_retained(self):
        result, arrays = audit_record(*fixture((0, 1, 5, 6)))
        self.assertTrue(result["identity_pass"] and result["native_clock_usable"] and result["usable"])
        self.assertFalse(result["cfr_eligible"])
        self.assertEqual(result["failures"], [])
        self.assertTrue(result["cfr_evidence"]["failures"])
        self.assertEqual(result["native_end_sec"], 0.7)
        terminal = result["terminal_evidence"]
        self.assertEqual(terminal["endpoint_authority"], "NATIVE_LAST_FRAME_PACKET_AND_DECORD_END")
        self.assertFalse(terminal["stream_header_matches_packet_terminal"])
        self.assertEqual(terminal["stream_header_integer_minus_packet_terminal_sec"], -0.1)
        self.assertEqual(arrays["native_frame_end_pts_ticks"], [1, 2, 6, 7])

    def test_noncfr_missing_packet_or_addendum_stops(self):
        row, numeric, prior, add, probe = fixture((0, 1, 5, 6))
        result, _ = audit_record(row, numeric, prior)
        self.assertTrue(result["identity_pass"])
        self.assertFalse(result["usable"])
        self.assertIsNone(result["native_end_sec"])
        del probe["frames"][-1]["pkt_duration"]
        result, _ = audit_record(row, numeric, prior, add, probe)
        self.assertFalse(result["usable"])
        self.assertIn("NATIVE_INTEGER_PTS_OR_PACKET_DURATION_MISSING", result["failures"])

    def test_native_all_integer_end_and_stream_start_tamper_refused(self):
        for mutation in ("pts", "end", "source", "stream", "text"):
            row, numeric, prior, add, probe = fixture((0, 1, 5, 6))
            if mutation == "pts": probe["frames"][1]["best_effort_timestamp"] += 1
            if mutation == "end": numeric["decord_timestamps"][-1][1] = f32(.8)
            if mutation == "source": add["source_sha256_after"] = "b" * 64
            if mutation == "stream": probe["streams"][0]["start_pts"] = 1
            if mutation == "text": probe["frames"][1]["best_effort_timestamp_time"] = "0.15"
            result, _ = audit_record(row, numeric, prior, add, probe)
            self.assertFalse(result["usable"], mutation)

    def test_shift_half_frame_and_dtype_not_tolerated(self):
        for mutation in ("half", "shift", "dtype", "epsilon"):
            row, numeric, prior, _, _ = fixture()
            if mutation == "half": numeric["decord_timestamps"][1][0] = f32(.15)
            if mutation == "shift": numeric["decord_timestamps"][1][0] = f32(.2)
            if mutation == "dtype": numeric["decord_timestamp_dtype"] = "float64"
            if mutation == "epsilon": numeric["decord_numeric_epsilon"] = 1e-3
            result, _ = audit_record(row, numeric, prior)
            self.assertFalse(result["identity_pass"], mutation)

    def test_exact_float32_binding_alias_and_fine_tick_diagnostic(self):
        expected = [Fraction(200), Fraction(200) + Fraction(1, 30), Fraction(200) + Fraction(2, 30)]
        evidence = bind_float32([f32(x) for x in expected], expected, Fraction(1, 90000))
        self.assertTrue(evidence["pass"])
        self.assertLess(evidence["direct_integer_tick_roundtrip_exact_count"], 3)
        with self.assertRaisesRegex(ValueError, "ALIAS"):
            bind_float32([f32(2**25), f32(2**25 + 1)], [Fraction(2**25), Fraction(2**25 + 1)], Fraction(1))
        with self.assertRaisesRegex(ValueError, "UNIQUELY"):
            reconstruct_integer_ticks([float(2**60)], Fraction(1))

    def test_nonzero_raw_and_relative_clock_are_explicit(self):
        row, numeric, prior, _, _ = fixture(origin=10)
        result, _ = audit_record(row, numeric, prior)
        self.assertEqual(result["decord_clock_mode"], "RAW_CONTAINER_PTS")
        numeric["decord_timestamps"] = [[f32(i / 10), f32((i + 1) / 10)] for i in range(4)]
        result, _ = audit_record(row, numeric, prior)
        self.assertTrue(result["usable"])
        self.assertEqual(result["decord_clock_mode"], "SOURCE_RELATIVE_PTS")

    def test_bound_real_failed_numeric_coarse_ticks_and_noncfr_stop(self):
        receipt = read_bound(RUN / "controller/pts_origin_v3_01_receipt.json", V3_RECEIPT_SHA)
        manifest = read_bound(RUN / "controller/m0_finalize_01/clean_manifest_426.json", REMATCH_SHA)
        rows = {r["video_id"]: r for r in manifest["records"]}
        priors = {r["video_id"]: r for r in receipt["records"]}
        for vid in receipt["failed_video_ids"]:
            path = RUN / "controller/pts_failed_numeric" / (vid + ".numeric.json")
            numeric = read_bound(path, priors[vid]["numeric_evidence_sha256"])
            result, arrays = audit_record(rows[vid], numeric, priors[vid])
            self.assertTrue(result["identity_pass"], (vid, result["failures"]))
            if vid in ("80", "161"):
                self.assertTrue(result["cfr_eligible"] and result["usable"], vid)
                self.assertFalse(result["decord_binding"]["whole_tick_used_as_float_error"])
            else:
                self.assertFalse(result["cfr_eligible"] or result["usable"], vid)
                self.assertIn("NONCFR_NATIVE_ENDPOINT_ADDENDUM_REQUIRED", result["failures"])
                self.assertIsNone(arrays["native_frame_end_pts_ticks"])

    def test_full_denominator_and_nontest_scopes_v2_writer(self):
        with tempfile.TemporaryDirectory(prefix="v4_cpu_", dir=HERE) as directory:
            root = Path(directory)
            manifest = {"kind": "REMATCH426", "expected_count": 426, "records": [{"video_id": str(i)} for i in range(426)]}
            records = [{"video_id": str(i), "usable": False, "identity_pass": False, "cfr_eligible": False,
                        "native_clock_usable": False} for i in range(426)]
            receipt = write_bundle(manifest, "a" * 64, "b" * 64, records, {}, root)
            self.assertEqual(receipt["audited_sources"], 426)
            self.assertEqual(len(receipt["failed_video_ids"]), 426)
            self.assertIsNone(receipt["clean_manifest"])
        with tempfile.TemporaryDirectory(prefix="v4_cpu_", dir=HERE) as directory:
            root = Path(directory)
            original = json.loads((RUN / "baseline_a/inputs/non_test_frozen8.json").read_text(encoding="utf-8"))
            scopes = [(r["scope_start_sec"], r["scope_end_sec"]) for r in original["records"]]
            records = [{"video_id": r["video_id"], "usable": True, "identity_pass": True, "cfr_eligible": True,
                        "native_clock_usable": False, "clock_branch": "CFR_LEGACY"} for r in original["records"]]
            write_bundle(original, "a" * 64, "b" * 64, records, {}, root)
            clean = json.loads((root / "clean_manifest_v2.json").read_text(encoding="utf-8"))
            self.assertEqual(scopes, [(r["scope_start_sec"], r["scope_end_sec"]) for r in clean["records"]])
            self.assertEqual(clean["schema"], "aic_rematch_A_input_v2")

    def test_production_stdlib_only_no_decode_invocation(self):
        for name in ("native_clock_core.py", "registry_io.py", "scan_native_clock.py", "build_nontest_registry.py"):
            tree = ast.parse((HERE / name).read_text(encoding="utf-8"))
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    self.assertFalse({v.name.split('.')[0] for v in node.names} & {"numpy", "torch", "decord", "subprocess"})
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn((node.module or '').split('.')[0], {"numpy", "torch", "decord", "subprocess"})

    def test_source_lock_rejects_modified_runtime(self):
        verify_source_lock()
        with tempfile.TemporaryDirectory(prefix="v4_cpu_", dir=HERE) as directory:
            root = Path(directory)
            for name in PRODUCTION_FILES | {"source_lock.json"}:
                (root / name).write_bytes((HERE / name).read_bytes())
            verify_source_lock(root)
            with (root / "native_clock_core.py").open("a", encoding="utf-8") as handle:
                handle.write("\n# mutated fixture\n")
            with self.assertRaisesRegex(ValueError, "SOURCE_LOCK_SHA_MISMATCH"):
                verify_source_lock(root)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(NativeClockCpuTests))
    report = {"status": "PASS_V4_STDLIB_CPU_ONLY" if result.wasSuccessful() else "FAIL_V4_CPU_TESTS",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
        "real_media_read": False, "media_redecoded": False, "models_run": False, "GPU_used": False,
        "real_bound_numeric_records_reaudited": 12, "full_426_numeric_scan_executed": False}
    (HERE / "cpu_test_receipt.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
