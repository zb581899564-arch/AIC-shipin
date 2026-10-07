#!/usr/bin/env python3
"""CPU-only validated teacher-record to optional-empty training-target bridge."""
from __future__ import annotations

import argparse
import copy
import hashlib
import importlib.util
import io
import json
from pathlib import Path
import sys
import unittest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE), str(HERE / "supervision")]
from training_target import from_teacher_record, target_text


def _supervision_fixture():
    source = HERE / "supervision" / "test_cpu.py"
    spec = importlib.util.spec_from_file_location("_training_bridge_supervision_fixture", source)
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


SUPERVISION = _supervision_fixture()


def make_record(mutate=None):
    window, observation, teacher, response = SUPERVISION.fixture()
    if mutate is not None:
        mutate(window, observation, teacher, response)
    return SUPERVISION.make_record(window, observation, teacher, json.dumps(response))


class TrainingTargetBridgeTests(unittest.TestCase):
    def test_positive_record_projects_only_complete_validated_target(self):
        record = make_record()
        self.assertEqual(record["status"], "PASS_WEAK_COMPLETE_WINDOW_TARGET")
        self.assertTrue(record["sft_eligible"])
        self.assertNotIn("all_provided_frames_reviewed", record["actual_observation"])
        self.assertTrue(record["parsed_answer"]["observation_scope"]["all_provided_frames_reviewed"])
        original = copy.deepcopy(record)
        label = from_teacher_record(record)
        self.assertEqual(label, {"observation_complete": True, "status": "OBSERVED_POSITIVE",
                                 "segments": [[2.0, 4.0]]})
        self.assertEqual(target_text(label, record["window"]["window_duration_sec"]), '{"segments":[[2,4]]}')
        self.assertEqual(record, original)

    def test_explicit_no_highlight_record_projects_legal_empty(self):
        def empty(window, observation, teacher, response):
            response.update(retained_segments=[], explicit_no_highlight=True,
                            decision_reason="No distinct highlight is visible in the provided samples")
        record = make_record(empty)
        self.assertEqual(record["status"], "PASS_WEAK_COMPLETE_WINDOW_TARGET")
        label = from_teacher_record(record)
        self.assertEqual(label, {"observation_complete": True, "status": "OBSERVED_EMPTY", "segments": []})
        self.assertEqual(target_text(label, record["window"]["window_duration_sec"]), '{"segments":[]}')

    def test_unknown_with_candidates_is_not_an_empty_or_positive_target(self):
        def uncertain(window, observation, teacher, response):
            response.update(uncertain=True, uncertainty_reasons=["Event boundary is not observable in the samples"])
        record = make_record(uncertain)
        self.assertEqual(record["status"], "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET")
        self.assertFalse(record["sft_eligible"])
        self.assertTrue(record["retained_segments"])
        with self.assertRaises(ValueError):
            from_teacher_record(record)

    def test_unknown_without_candidates_does_not_certify_empty(self):
        def uncertain(window, observation, teacher, response):
            response.update(retained_segments=[], explicit_no_highlight=False, uncertain=True,
                            uncertainty_reasons=["Provided observations are ambiguous"])
        record = make_record(uncertain)
        self.assertEqual(record["status"], "EXCLUDED_UNCERTAIN_NOT_AN_EMPTY_TARGET")
        self.assertFalse(record["sft_eligible"])
        with self.assertRaises(ValueError):
            from_teacher_record(record)

    def test_teacher_not_reviewing_all_samples_is_rejected(self):
        def unreviewed(window, observation, teacher, response):
            response["observation_scope"]["all_provided_frames_reviewed"] = False
        record = make_record(unreviewed)
        self.assertEqual(record["status"], "INVALID_TEACHER_OR_INPUT_RECEIPT")
        self.assertFalse(record["sft_eligible"])
        with self.assertRaises(ValueError):
            from_teacher_record(record)

    def test_bridge_checks_both_delivery_and_review_fields_even_with_pass_flags(self):
        valid = make_record()
        for field in ("delivery", "review"):
            record = copy.deepcopy(valid)
            if field == "delivery":
                record["actual_observation"]["all_planned_frames_delivered"] = False
            else:
                record["parsed_answer"]["observation_scope"]["all_provided_frames_reviewed"] = False
            with self.subTest(field=field), self.assertRaises(ValueError):
                from_teacher_record(record)

    def test_unrepresentable_endpoint_is_explicit_consumer_rejection(self):
        def precision(window, observation, teacher, response):
            response["retained_segments"][0]["start_sec"] = 2.00001
        record = make_record(precision)
        self.assertEqual(record["status"], "PASS_WEAK_COMPLETE_WINDOW_TARGET")
        self.assertTrue(record["sft_eligible"])
        original = copy.deepcopy(record)
        with self.assertRaisesRegex(ValueError, "four-decimal"):
            from_teacher_record(record)
        self.assertEqual(record, original)
        self.assertEqual(json.loads(record["target_json"])["segments"], [[2.00001, 4.0]])

    def test_representable_four_decimal_endpoint_remains_unchanged(self):
        def precision(window, observation, teacher, response):
            response["retained_segments"][0]["start_sec"] = 2.0001
        record = make_record(precision)
        label = from_teacher_record(record)
        self.assertEqual(label["segments"], [[2.0001, 4.0]])
        self.assertEqual(target_text(label, record["window"]["window_duration_sec"]),
                         '{"segments":[[2.0001,4]]}')

    def test_ineligible_or_uncertain_pass_record_is_rejected(self):
        valid = make_record()
        for mutation in ({"sft_eligible": False}, {"uncertain": True}, {"status": "UNKNOWN"}):
            record = {**valid, **mutation}
            with self.subTest(mutation=mutation), self.assertRaises(ValueError):
                from_teacher_record(record)

    def test_empty_flag_and_target_disagreement_is_rejected(self):
        record = make_record()
        record["explicit_no_highlight"] = True
        with self.assertRaises(ValueError):
            from_teacher_record(record)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path)
    args = parser.parse_args()
    if args.output is not None and args.output.exists():
        raise FileExistsError("preserve CPU bridge evidence")
    stream = io.StringIO()
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(TrainingTargetBridgeTests)
    result = unittest.TextTestRunner(stream=stream, verbosity=2).run(suite)
    receipt = {"schema": "aic_training_target_bridge_cpu_v1", "status": "PASS" if result.wasSuccessful() else "FAIL",
               "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
               "output": stream.getvalue(), "source_sha256": {
                   str(path.relative_to(HERE)): hashlib.sha256(path.read_bytes()).hexdigest()
                   for path in (HERE / "training_target.py", HERE / "contracts.py", Path(__file__),
                                HERE / "supervision" / "validate_teacher.py", HERE / "supervision" / "test_cpu.py")},
               "fixture_only": True, "supervision_record_mutated": False,
               "model_run": False, "GPU_used": False, "contest_media_read": False,
               "semantic_labels_read": False, "quality_claim": False}
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
