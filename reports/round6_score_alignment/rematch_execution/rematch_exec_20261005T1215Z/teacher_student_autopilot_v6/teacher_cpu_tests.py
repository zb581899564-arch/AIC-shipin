"""CPU engineering contracts. Synthetic fixtures never certify teacher quality."""
import copy
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
from pathlib import Path
import tempfile
import threading
import unittest

import teacher_label as teacher

RUN = Path(__file__).resolve().parent.parent
VALIDATOR = teacher.validator_for(RUN)


def fixture(split="train", identity="synthetic_train"):
    window = {"schema": "aic_complete_window_selection_v1", "split": split, "window_id": identity,
        "source_group": identity, "youtube_id": identity,
        "source_path": "/home/inspur/aic_video_data/videos/s/" + identity + ".mp4",
        "source_sha256": "a" * 64, "clock_sequence_sha256": "b" * 64,
        "window_pts_start_sec": 10.25, "window_pts_end_exclusive_sec": 40.25, "window_duration_sec": 30.0,
        "planned_actual_pts_sec": [10.25, 25.25, 40.0], "planned_source_frame_ordinals": [100, 400, 695],
        "first_eligible_pts_sec": 10.25, "last_eligible_pts_sec": 40.0, "structural_stratum": "source_beginning"}
    observation = {**{k: window[k] for k in ("window_id", "source_path", "source_sha256", "clock_sequence_sha256")},
        "decode_status": "PASS_REAL_SEQUENTIAL_DECODE", "pixel_identity_status": "PASS", "all_planned_frames_delivered": True,
        "source_frame_ordinals": window["planned_source_frame_ordinals"], "actual_pts_sec": window["planned_actual_pts_sec"],
        "frame_pixel_sha256": ["c" * 64] * 3, "input_contract_sha256": "d" * 64,
        "actual_processed_pixels_per_frame": [589824] * 3, "max_pixels_per_frame": 786432,
        "max_sequence_length": 65536, "input_sequence_length": 2000, "max_frames": 64,
        "source_total_frames": 1000, "fps_num": 20, "fps_den": 1, "width": 1920, "height": 1080}
    identity_receipt = {"base_model_id": teacher.BASE_ID, "model_id": teacher.TEACHER_ID,
        "model_revision": teacher.TEACHER_REVISION, "inference_status": "PASS_REAL_TEACHER_GENERATION",
        "production_test_access": False, "capacity_admission_pass": True, "job_source_lock_sha256": "e" * 64,
        "weight_files": [{"path": "SYNTHETIC_CPU_FIXTURE_ONLY/Qwen3VL-32B-Instruct-Q4_K_M.gguf",
            "sha256": "5cf0136e721d6294718ec71fd8c93b17ab5dd4e2714d6079e83fa46571ad94c8"},
            {"path": "SYNTHETIC_CPU_FIXTURE_ONLY/mmproj-Qwen3VL-32B-Instruct-F16.gguf",
            "sha256": "8617824839df91f84b4840ad5084dcf50a1403a435a1f4cfc4d8c84ce6cac2fc"}],
        "runtime_revision": "SYNTHETIC_CPU_FIXTURE_ONLY", "generated_utc": "2026-10-07T00:00:00Z",
        "prompt_sha256": teacher.text_sha(VALIDATOR.prompt_for(window, observation))}
    response = {"window_id": identity, "observation_scope": {"window_pts_start_sec": 10.25,
        "window_pts_end_exclusive_sec": 40.25, "sampled_pts_sec": observation["actual_pts_sec"], "all_provided_frames_reviewed": True},
        "retained_segments": [{"start_sec": 0, "end_sec": 1.25, "reason": "Synthetic boundary event for contract test only"},
            {"start_sec": 15, "end_sec": 16, "reason": "Synthetic distinct second event for contract test only"}],
        "explicit_no_highlight": False, "uncertain": False, "uncertainty_reasons": [],
        "decision_reason": "Synthetic test response; not evidence of actual teacher quality", "boundary_notes": ["Synthetic left-boundary contract test"]}
    return window, observation, identity_receipt, response


class TeacherContracts(unittest.TestCase):
    def record(self, response_change=None, observation_change=None):
        window, observation, identity, response = fixture()
        if response_change:
            response.update(response_change)
        if observation_change:
            observation.update(observation_change)
        return VALIDATOR.make_record(window, observation, identity, json.dumps(response))

    def test_failure_missing_unknown_and_false_empty_never_negative(self):
        for change in ({"retained_segments": []}, {"retained_segments": [], "uncertain": True,
            "uncertainty_reasons": ["Incomplete observation"], "explicit_no_highlight": True}):
            record = self.record(change)
            self.assertFalse(record["sft_eligible"])
            self.assertIsNone(record["target_json"])
        window, observation, identity, _ = fixture()
        for raw in (None, "", "not JSON", '{"window_id":"x","window_id":"y"}'):
            self.assertFalse(VALIDATOR.make_record(window, observation, identity, raw)["sft_eligible"])
        record = self.record({"retained_segments": [], "uncertain": True, "uncertainty_reasons": ["Unseen gap"]})
        self.assertEqual(record["status"], "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET")

    def test_justified_empty_and_multisegment_boundaries_project_without_repair(self):
        positive = self.record()
        self.assertTrue(positive["sft_eligible"])
        self.assertEqual(json.loads(positive["target_json"])["segments"], [[0, 1.25], [15, 16]])
        empty = self.record({"retained_segments": [], "explicit_no_highlight": True, "decision_reason": "Synthetic ordinary-background test only"})
        self.assertEqual(empty["target_json"], '{"segments":[]}')
        illegal = self.record({"retained_segments": [{"start_sec": 0, "end_sec": 31, "reason": "Out of window"}]})
        self.assertFalse(illegal["sft_eligible"])
        over_five = self.record({"retained_segments": [{"start_sec": i * 2, "end_sec": i * 2 + 1, "reason": "Synthetic event"} for i in range(6)]})
        self.assertEqual(over_five["status"], "EXCLUDED_UNREPRESENTABLE_SEGMENT_COUNT")
        self.assertEqual(len(over_five["parsed_answer"]["retained_segments"]), 6)

    def test_native_pts_and_rgb_receipts_cannot_be_missing_or_misbound(self):
        window, observation, _, _ = fixture()
        teacher.verify_decoded_pts(observation["source_frame_ordinals"], observation["actual_pts_sec"], window)
        for ordinals, points in (([100, 400, 695], [10.25, 25.25, 39]), ([100, 401, 695], observation["actual_pts_sec"])):
            with self.assertRaises(ValueError):
                teacher.verify_decoded_pts(ordinals, points, window)
        for change in ({"frame_pixel_sha256": []}, {"all_planned_frames_delivered": False}, {"input_sequence_length": 65537}):
            self.assertFalse(self.record(observation_change=change)["sft_eligible"])

    def test_source_isolation_and_contest_path_rejection(self):
        window, *_ = fixture()
        dev = dict(window, split="dev", source_path="/home/inspur/aic_video_data/videos/other.mp4")
        with self.assertRaises(ValueError):
            VALIDATOR.validate_isolation([window], [dev])
        for path in ("/home/inspur/aic_video_work/contest/test.mp4", "/home/inspur/aic_video_data/videos/../contest/test.mp4"):
            with self.assertRaises(ValueError):
                VALIDATOR.validate_window(dict(window, source_path=path))

    def test_real_processor_log_required_and_temporal_copies_distinguished(self):
        log = "\n".join(f"clip_image_batch_encode: copying image {i}/2 to input buffer (nx=1024, ny=576)" for _ in range(3) for i in (1, 2))
        grids = teacher.parse_processor_log(log, 3)
        self.assertEqual([g["pixels"] for g in grids], [589824] * 3)
        self.assertEqual([g["tensor_copies"] for g in grids], [2] * 3)
        for invalid in ("", log.replace("nx=1024", "nx=1023"), log + log, log.replace("image 2/2", "image 1/2")):
            with self.assertRaises(ValueError):
                teacher.parse_processor_log(invalid, 3)

    def test_no_remote_server_or_redirectable_external_url(self):
        self.assertEqual(teacher.local_url("http://127.0.0.1:8080/v1"), "http://127.0.0.1:8080")
        for url in ("https://127.0.0.1:8080", "http://example.com:8080", "http://127.0.0.1:8080?target=example.com", "http://localhost:8080"):
            with self.assertRaises(ValueError):
                teacher.local_url(url)

    def test_review_raw_contradiction_and_scope_mismatch_stop(self):
        record = self.record()
        value = {"window_id": record["window_id"], "observation_scope": record["parsed_answer"]["observation_scope"],
            "semantics_consistent": True, "uncertain": False, "reason": "Synthetic contract review only", "issues": []}
        teacher.review_response(json.dumps(value), record, VALIDATOR)
        for change in ({"semantics_consistent": False}, {"uncertain": True}, {"issues": ["Event unsupported"]}, {"window_id": "foreign"}):
            with self.assertRaises(ValueError):
                teacher.review_response(json.dumps({**value, **change}), record, VALIDATOR)

    def test_shortages_and_all_empty_stop_without_forcing_quota(self):
        record = self.record({"retained_segments": [], "explicit_no_highlight": True})
        validation = VALIDATOR.summarize([record])
        reasons, audit = teacher.semantic_audit([record], validation)
        self.assertTrue(any("20-update" in reason for reason in reasons))
        self.assertTrue(any("all-empty" in reason for reason in reasons))
        self.assertTrue(audit["no_observed_class_manufactured"])

    def test_http_and_json_errors_preserve_original_bytes(self):
        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                self.rfile.read(int(self.headers["Content-Length"]))
                self.send_response(503 if self.path == "/failed" else 200)
                self.end_headers(); self.wfile.write(b"ORIGINAL_FAILURE_BODY" if self.path == "/failed" else b"not-json")
            def log_message(self, *args):
                pass
        server = HTTPServer(("127.0.0.1", 0), Handler)
        thread = threading.Thread(target=server.serve_forever, daemon=True); thread.start()
        try:
            with tempfile.TemporaryDirectory(prefix="teacher_cpu_http_", dir=teacher.HERE) as folder:
                for route, expected in (("failed", b"ORIGINAL_FAILURE_BODY"), ("json", b"not-json")):
                    path = Path(folder) / route
                    with self.assertRaises((ValueError, json.JSONDecodeError)):
                        teacher.http_json(f"http://127.0.0.1:{server.server_port}/{route}", {"synthetic": True}, path, timeout=5)
                    self.assertEqual((path / "response.bin").read_bytes(), expected)
        finally:
            server.shutdown(); server.server_close(); thread.join(timeout=5)

    def test_unmodified_independent_validator_real_subprocess_receipt_chain(self):
        with tempfile.TemporaryDirectory(prefix="teacher_cpu_validator_", dir=teacher.HERE) as folder:
            root = Path(folder)
            train, dev = fixture(), fixture("dev", "synthetic_dev")
            dev[3].update(retained_segments=[], explicit_no_highlight=True, decision_reason="Synthetic empty test only")
            teacher.save_rows(root / "selected_train.jsonl", [train[0]])
            teacher.save_rows(root / "selected_dev.jsonl", [dev[0]])
            teacher.save(root / "selection_receipt.json", {"status": "PASS_CPU_SELECTION_UNLABELLED", "confirm_opened": False,
                "contest_assets_opened": False, "files": {name: teacher.sha(root / name) for name in ("selected_train.jsonl", "selected_dev.jsonl")}}, fresh=True)
            annotations = [{"window_id": data[0]["window_id"], "observation": data[1], "teacher": data[2], "raw_answer": json.dumps(data[3])} for data in (train, dev)]
            teacher.save_rows(root / "annotations.jsonl", annotations)
            receipt = teacher.independent_validation(RUN, root / "selected_train.jsonl", root / "selected_dev.jsonl", root / "selection_receipt.json", root / "annotations.jsonl", root / "validated")
            self.assertEqual(receipt["eligible_by_split"], {"train": 1, "dev": 1})
            self.assertEqual(receipt["unlabelled_window_count"], 0)
            self.assertEqual(receipt["explicit_empty_by_split"], {"train": 0, "dev": 1})
            self.assertEqual(teacher.rows(root / "validated/eligible_dev.jsonl")[0]["target_json"], '{"segments":[]}')
            self.assertFalse(receipt["semantic_training_admitted"])


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TeacherContracts)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    print(json.dumps({"status": "PASS_CPU_TEACHER_CONTRACTS" if result.wasSuccessful() else "STOP_CPU_TEACHER_CONTRACTS",
        "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors), "real_teacher_quality_tested": False,
        "gpu_used": False, "synthetic_receipts_not_for_admission": True}, ensure_ascii=False))
    raise SystemExit(0 if result.wasSuccessful() else 1)
