"""Pure CPU spatial-field tests using synthetic identities and boxes only."""
from copy import deepcopy
import hashlib
import json
from pathlib import Path
import sys
import unittest

sys.dont_write_bytecode = True
sys.path.insert(0, str(Path(__file__).resolve().parent.parent / "baseline_a_pts_v1" / "vendor"))
from field_contract import build_field_requests, compose_from_field


def digest(row):
    value = {key: row[key] for key in sorted(row) if key != "anchor_request_sha256"}
    return hashlib.sha256(json.dumps(value, ensure_ascii=False, sort_keys=True,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


class FieldContractTests(unittest.TestCase):
    def setUp(self):
        self.manifest = {
            "schema": "aic_rematch_A_input_v1", "kind": "NONTEST_FROZEN8", "expected_count": 8,
            "allowed_source_roots": ["/synthetic-approved"],
            "input_contract": {
                "status": "APPROVED_METADATA_ONLY", "data_use_evidence": "SYNTHETIC_TEST_ONLY",
                "target_ratio_evidence": "SYNTHETIC_TEST_ONLY", "metadata_role_evidence": "SYNTHETIC_TEST_ONLY",
            },
            "records": [],
        }
        self.frames, self.shots = [], []
        for number in range(8):
            vid = str(number)
            ratio = [9, 16] if number % 2 == 0 else [16, 9]
            source_path = "/synthetic-approved/" + vid + ".mp4"
            self.manifest["records"].append({
                "video_id": vid, "source_group": "synthetic-" + vid,
                "source_path": source_path, "source_sha256": hashlib.sha256(vid.encode()).hexdigest(),
                "width": 160, "height": 160, "n_frames": 20, "fps_num": 10, "fps_den": 1,
                "targetRatioWH": ratio, "scope_start_sec": 0, "scope_end_sec": 2,
            })
            for frame in range(20):
                self.frames.append({"video_id": vid, "source_frame": frame, "source_path": source_path,
                                    "source_width": 160, "source_height": 160, "source_n_frames": 20,
                                    "fps": 10.0, "target_ratio_wh": list(ratio)})
                self.shots.append({"video_id": vid, "source_frame": frame,
                                   "is_shot_start": frame in (0, 10),
                                   "decoded_pixel_sha256": hashlib.sha256((vid + ":" + str(frame)).encode()).hexdigest()})
        self.requests = build_field_requests(self.frames, self.shots)
        self.outputs = []
        for request in self.requests:
            frame = request["source_frame"]
            x = frame * 2 if frame < 10 else 100 - frame * 2
            self.outputs.append({"video_id": request["video_id"], "source_frame": frame,
                                 "status": "MODEL_OK", "used_fallback": False,
                                 "spatial_source": "QWEN_ANCHOR_SAME_FRAME", "box_xyw": [x, 2, 54],
                                 "anchor_request_sha256": request["anchor_request_sha256"],
                                 "decoded_pixel_sha256": request["expected_pixel_sha256"]})

    def selected(self, frames, vid="0"):
        return [deepcopy(row) for row in self.frames if row["video_id"] == vid and row["source_frame"] in frames]

    def compose(self, selected=None, shots=None, requests=None, outputs=None):
        return compose_from_field(self.manifest, self.selected([5]) if selected is None else selected,
                                  self.shots if shots is None else shots,
                                  self.requests if requests is None else requests,
                                  self.outputs if outputs is None else outputs)

    def test_common_frame_box_and_provenance_identical_across_selections(self):
        first, first_prov = self.compose(self.selected([0, 5, 9, 10, 15, 19]))
        second, second_prov = self.compose(self.selected([4, 5, 6, 15]))
        first_boxes = {(row["video_id"], item["frame"]): item["bboxes"]
                       for row in first for item in row["predictions"]}
        second_boxes = {(row["video_id"], item["frame"]): item["bboxes"]
                        for row in second for item in row["predictions"]}
        first_sources = {(row["video_id"], row["source_frame"]): row for row in first_prov}
        second_sources = {(row["video_id"], row["source_frame"]): row for row in second_prov}
        for key in first_boxes.keys() & second_boxes.keys():
            self.assertEqual(first_boxes[key], second_boxes[key])
            self.assertEqual(first_sources[key], second_sources[key])

    def test_selection_discontinuity_does_not_change_field_anchors(self):
        original = deepcopy(self.requests)
        for chosen in ([1, 2, 17, 18], [4, 5, 6], [9, 10], []):
            self.compose(self.selected(chosen))
            self.assertEqual(self.requests, original)
        self.assertEqual([r["source_frame"] for r in self.requests if r["video_id"] == "0"], [0, 8, 9, 10, 18, 19])

    def test_interpolation_cannot_cross_actual_shot(self):
        rows, provenance = self.compose(self.selected([7, 9, 10, 11]))
        by_frame = {row["source_frame"]: row for row in provenance}
        self.assertEqual(by_frame[7]["right_anchor"], 8)
        self.assertEqual(by_frame[9]["left_anchor"], 9)
        self.assertEqual(by_frame[10]["right_anchor"], 10)
        self.assertEqual((by_frame[11]["left_anchor"], by_frame[11]["right_anchor"]), (10, 18))
        self.assertNotEqual(by_frame[9]["shot_id"], by_frame[10]["shot_id"])
        self.assertEqual(rows[0]["predictions"][0]["bboxes"], [14, 2, 54])

    def test_legal_empty_selection_keeps_all_video_rows(self):
        rows, provenance = self.compose([])
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["predictions"] == [] for row in rows))
        self.assertEqual(provenance, [])

    def test_empty_field_and_selection_no_divide_by_zero(self):
        self.assertEqual(build_field_requests([], []), [])
        rows, provenance = self.compose([], [], [], [])
        self.assertEqual(len(rows), 8)
        self.assertTrue(all(row["predictions"] == [] for row in rows))
        self.assertEqual(provenance, [])

    def test_single_field_frame_is_its_own_endpoint(self):
        frames = self.selected([5])
        shots = [deepcopy(row) for row in self.shots if row["video_id"] == "0" and row["source_frame"] == 5]
        requests = build_field_requests(frames, shots)
        output = deepcopy(self.outputs[0])
        output.update(source_frame=5, box_xyw=[10, 2, 54], anchor_request_sha256=requests[0]["anchor_request_sha256"],
                      decoded_pixel_sha256=requests[0]["expected_pixel_sha256"])
        rows, provenance = self.compose(frames, shots, requests, [output])
        self.assertEqual(rows[0]["predictions"], [{"frame": 5, "bboxes": [10, 2, 54]}])
        self.assertEqual(provenance[0]["spatial_source"], "QWEN_ANCHOR_SAME_FRAME")

    def test_every_video_returned_but_provenance_only_selected(self):
        rows, provenance = self.compose(self.selected([5, 15]))
        self.assertEqual([row["video_id"] for row in rows], [str(i) for i in range(8)])
        self.assertEqual([(row["video_id"], row["source_frame"]) for row in provenance], [("0", 5), ("0", 15)])
        self.assertTrue(all(row["predictions"] == [] for row in rows[1:]))

    def test_missing_endpoint_or_intermediate_request_rejected(self):
        for frame in (0, 8, 9, 10, 18, 19):
            with self.subTest(frame=frame):
                requests = [r for r in self.requests if (r["video_id"], r["source_frame"]) != ("0", frame)]
                outputs = [r for r in self.outputs if (r["video_id"], r["source_frame"]) != ("0", frame)]
                with self.assertRaisesRegex(ValueError, "anchor schedule"):
                    self.compose(requests=requests, outputs=outputs)

    def test_missing_output_rejected(self):
        with self.assertRaisesRegex(ValueError, "key coverage"):
            self.compose(outputs=self.outputs[:-1])

    def test_failed_unselected_anchor_still_rejected(self):
        for selected in (self.selected([5]), []):
            outputs = deepcopy(self.outputs)
            outputs[-1]["status"] = "PARSE_FAILURE"
            with self.assertRaisesRegex(ValueError, "anchor failure"):
                self.compose(selected, outputs=outputs)

    def test_bad_request_hash_even_when_output_matches_rejected(self):
        requests, outputs = deepcopy(self.requests), deepcopy(self.outputs)
        requests[0]["anchor_request_sha256"] = "0" * 64
        outputs[0]["anchor_request_sha256"] = "0" * 64
        with self.assertRaisesRegex(ValueError, "request SHA256"):
            self.compose(requests=requests, outputs=outputs)

    def test_rehashed_request_with_wrong_pixel_identity_rejected(self):
        requests, outputs = deepcopy(self.requests), deepcopy(self.outputs)
        requests[0]["expected_pixel_sha256"] = "0" * 64
        requests[0]["anchor_request_sha256"] = digest(requests[0])
        outputs[0]["anchor_request_sha256"] = requests[0]["anchor_request_sha256"]
        outputs[0]["decoded_pixel_sha256"] = requests[0]["expected_pixel_sha256"]
        with self.assertRaisesRegex(ValueError, "pixel identity"):
            self.compose(requests=requests, outputs=outputs)

    def test_wrong_output_sha_pixel_or_status_rejected(self):
        for name, value in (("anchor_request_sha256", "0" * 64), ("decoded_pixel_sha256", "0" * 64),
                            ("status", "DECODE_OR_MODEL_FAILURE"), ("used_fallback", True),
                            ("spatial_source", "EXTERNAL_BOX"), ("box_xyw", [-1, 2, 54]),
                            ("box_xyw", [True, 2, 54])):
            with self.subTest(name=name, value=value):
                outputs = deepcopy(self.outputs)
                outputs[0][name] = value
                with self.assertRaisesRegex(ValueError, "anchor failure"):
                    self.compose(outputs=outputs)

    def test_selected_outside_field_rejected(self):
        outside = self.selected([5])
        outside[0]["source_frame"] = 20
        with self.assertRaisesRegex(ValueError, "outside the registered field"):
            self.compose(outside)

    def test_selected_source_identity_mismatch_rejected(self):
        for name, value in (("source_path", "/unregistered/a.mp4"), ("source_width", 161),
                            ("fps", 11), ("target_ratio_wh", [16, 9])):
            with self.subTest(name=name):
                chosen = self.selected([5])
                chosen[0][name] = value
                with self.assertRaisesRegex(ValueError, "source identity"):
                    self.compose(chosen)

    def test_field_shots_must_cover_exact_frame_domain(self):
        with self.assertRaisesRegex(ValueError, "exactly cover"):
            build_field_requests(self.frames, self.shots[:-1])
        with self.assertRaisesRegex(ValueError, "duplicate"):
            build_field_requests(self.frames, self.shots + [self.shots[0]])

    def test_missing_or_invalid_shot_pixel_hash_rejected(self):
        for value in (None, "bad", "z" * 64):
            with self.subTest(value=value):
                shots = deepcopy(self.shots)
                shots[5]["decoded_pixel_sha256"] = value
                with self.assertRaisesRegex(ValueError, "pixel SHA256"):
                    build_field_requests(self.frames, shots)

    def test_non_bool_shot_flag_rejected(self):
        shots = deepcopy(self.shots)
        shots[5]["is_shot_start"] = "False"
        with self.assertRaisesRegex(ValueError, "explicit bool"):
            build_field_requests(self.frames, shots)

    def test_schedule_cannot_ignore_new_actual_shot_boundary(self):
        shots = deepcopy(self.shots)
        shots[5]["is_shot_start"] = True
        with self.assertRaisesRegex(ValueError, "anchor schedule"):
            self.compose(shots=shots)

    def test_field_frame_unknown_fields_do_not_become_external_boxes(self):
        frames = deepcopy(self.frames)
        frames[0]["external_box"] = [0, 0, 54]
        with self.assertRaisesRegex(ValueError, "unregistered fields"):
            build_field_requests(frames, self.shots)

    def test_request_unknown_fields_rejected_even_with_valid_hash(self):
        requests = deepcopy(self.requests)
        requests[0]["external_box"] = [0, 0, 54]
        requests[0]["anchor_request_sha256"] = digest(requests[0])
        with self.assertRaisesRegex(ValueError, "unregistered fields"):
            self.compose(requests=requests)

    def test_fixed_max_gap_and_exact_frame_integer_contract(self):
        for max_gap in (True, 0, 4, 9, 8.0):
            with self.subTest(max_gap=max_gap):
                with self.assertRaisesRegex(ValueError, "max gap is 8"):
                    build_field_requests(self.frames, self.shots, max_gap)
        for value in (True, -1, 1.5):
            with self.subTest(frame=value):
                frames = deepcopy(self.frames)
                frames[0]["source_frame"] = value
                with self.assertRaisesRegex(ValueError, "source-frame identity"):
                    build_field_requests(frames, self.shots)

    def test_builder_and_composer_do_not_mutate_inputs(self):
        before = deepcopy((self.frames, self.shots, self.requests, self.outputs))
        build_field_requests(self.frames, self.shots)
        self.compose(self.selected([5, 15]))
        self.assertEqual((self.frames, self.shots, self.requests, self.outputs), before)


if __name__ == "__main__":
    unittest.main()
