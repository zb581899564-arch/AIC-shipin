"""Additional v8 CPU engineering checks; genuine 8B CUDA acceptance remains required."""
from pathlib import Path
import copy
from collections import Counter
import json
import random
import tempfile
import unittest

import train_student as student


class V8StudentContracts(unittest.TestCase):
    def test_prefix_configuration_and_partial_position(self):
        batches = student.schedule(96)
        self.assertEqual(student.prefix_update_count(batches, 2), 2)
        self.assertEqual(student.prefix_update_count(batches, 3), 3)
        self.assertEqual(student.prefix_update_count(batches, 4), 4)
        for bad in (1, 5, True, 4.0):
            with self.assertRaises(ValueError):
                student.prefix_update_count(batches, bad)
        position = student.prefix_resume_position(batches, 4, dict(checkpoints=[], devmetrics=[]))
        self.assertEqual(position["next_schedule_index"], 4)
        self.assertEqual(position["pending_phase"], "NEXT_TRAIN_BATCH")
        self.assertEqual(position["entire_schedule"], batches)
        position["entire_schedule"][4]["indices"][0] = -1
        self.assertNotEqual(position["entire_schedule"], batches)

    def test_saved_prefix_inspection_has_exact_same_continuation_as_uninterrupted_cpu_adamw(self):
        import numpy as np
        import torch
        batches = student.schedule(96)

        def execute(inspect):
            random.seed(37); np.random.seed(37); torch.manual_seed(37)
            parameter = torch.nn.Parameter(torch.tensor([.25, -.5]))
            optimizer = torch.optim.AdamW([parameter], lr=1e-5, betas=(.9, .999), eps=1e-8, weight_decay=0)
            identities = (id(parameter), id(optimizer))
            loss_values = []
            with tempfile.TemporaryDirectory(prefix="aic-v8-continuity-") as temporary:
                for update, batch in enumerate(batches, 1):
                    optimizer.zero_grad(set_to_none=True)
                    noise = torch.rand(2) + random.random() + float(np.random.random())
                    loss = (parameter * noise).square().mean()
                    self.assertTrue(bool(torch.isfinite(loss)))
                    loss.backward(); self.assertTrue(bool(torch.isfinite(parameter.grad).all()))
                    optimizer.step(); loss_values.append(float(loss))
                    if inspect and update == student.prefix_update_count(batches):
                        state = dict(optimizer=copy.deepcopy(optimizer.state_dict()),
                            lora={"lora_fixture": parameter.detach().clone()}, optimizer_parameter_name_order=["lora_fixture"],
                            **student.rng_snapshot(torch, np, cuda=False),
                            **student.prefix_resume_position(batches, update, dict(checkpoints=[], devmetrics=[])))
                        path = Path(temporary) / "prefix_state.pt"
                        torch.save(state, path)
                        student.trusted_state_roundtrip(path, state, optimizer, [("lora_fixture", parameter)], torch, np, cuda=False)
                        self.assertEqual((id(parameter), id(optimizer)), identities)
                return parameter.detach().clone(), copy.deepcopy(optimizer.state_dict()), loss_values, student.rng_snapshot(torch, np, cuda=False)

        reference = execute(False)
        inspected = execute(True)
        student.assert_tree_equal(reference, inspected, torch, np, "full_continuation")
        self.assertEqual(len(inspected[2]), 18)
        self.assertEqual(next(iter(inspected[1]["state"].values()))["step"].item(), 18)

    def test_baseline_zero_wins_ties_and_beats_worse_new_epoch(self):
        baseline = dict(epoch=0, video_macro_f1=.6, adapter_dir="original_B")
        worse = dict(epoch=1, video_macro_f1=.55, adapter_dir="T1")
        tied = dict(epoch=2, video_macro_f1=.6, adapter_dir="T2")
        self.assertEqual(student.select_checkpoint([baseline, worse, tied]), baseline)
        better = dict(epoch=3, video_macro_f1=.61, adapter_dir="T3")
        self.assertEqual(student.select_checkpoint([baseline, worse, tied, better]), better)
        with self.assertRaisesRegex(ValueError, "candidate zero"):
            student.select_checkpoint([better])

    def test_positive_only_data_is_admitted_without_inventing_empty_supervision(self):
        target = dict(explicit_no_highlight=False, target_json=json.dumps(dict(segments=[[0, 1]])))
        result = student.supervision_classes([target])
        self.assertEqual(result["positive"], 1)
        self.assertEqual(result["explicit_no_highlight"], 0)
        self.assertFalse(result["rejection_supervision_available"])
        self.assertFalse(result["whole_window_rejection_learning_claim"])
        with self.assertRaisesRegex(ValueError, "NO_POSITIVE_SUPERVISION"):
            student.supervision_classes([dict(explicit_no_highlight=True, target_json='{"segments":[]}')])
        with self.assertRaises(ValueError):
            student.supervision_classes([dict(explicit_no_highlight=False, target_json='{"segments":[]}')])

    def test_legal_all_empty_dev_reference_is_not_a_collapse_by_itself(self):
        summary = dict(windows=2, legal_empty_windows=2, all_selected_windows=0,
            reference_positive_windows=0, group_f1=dict(a=1.0, b=1.0), video_macro_f1=1.0)
        rule = dict(widespread_degraded_group_fraction=.75, widespread_macro_f1_drop=.05)
        self.assertIsNone(student.dev_failure(summary, None, rule))
        summary["reference_positive_windows"] = 1
        self.assertEqual(student.dev_failure(summary, None, rule), "STOP_T_SYSTEMATIC_ALL_EMPTY_DEV")

    def test_v2_consumer_checks_all_raws_including_unknown_and_exact_class_denominators(self):
        # These are protocol fixtures only. They certify no visual quality.
        import teacher_label as teacher
        validator = teacher.validator_for(Path(__file__).resolve().parent.parent)
        records = {}; reviews = []; eligible = []
        for index, (state, split) in enumerate((("KEEP", "train"), ("NO_HIGHLIGHT", "dev"), ("UNKNOWN", "train"))):
            wid = "SYNTHETIC_CPU_CONTRACT_ONLY_" + str(index)
            window = dict(schema="aic_complete_window_selection_v1", split=split, window_id=wid,
                source_group=wid, youtube_id=wid, source_path="/home/inspur/aic_video_data/videos/s/" + wid + ".mp4",
                source_sha256="a" * 64, clock_sequence_sha256="b" * 64, window_pts_start_sec=10.25,
                window_pts_end_exclusive_sec=40.25, window_duration_sec=30.0,
                planned_actual_pts_sec=[10.25, 25.25, 40.0], planned_source_frame_ordinals=[100, 400, 695],
                first_eligible_pts_sec=10.25, last_eligible_pts_sec=40.0, structural_stratum="source_beginning")
            observation = dict(window_id=wid, source_path=window["source_path"], source_sha256=window["source_sha256"],
                clock_sequence_sha256=window["clock_sequence_sha256"], window_pts_start_sec=10.25,
                window_pts_end_exclusive_sec=40.25, window_duration_sec=30.0,
                decode_status="PASS_REAL_SEQUENTIAL_DECODE", pixel_identity_status="PASS", all_planned_frames_delivered=True,
                source_frame_ordinals=window["planned_source_frame_ordinals"], actual_pts_sec=window["planned_actual_pts_sec"],
                frame_pixel_sha256=["c" * 64] * 3, input_contract_sha256="d" * 64,
                actual_processed_pixels_per_frame=[589824] * 3, max_pixels_per_frame=786432,
                max_sequence_length=65536, input_sequence_length=2000, max_frames=64,
                source_total_frames=1000, fps_num=20, fps_den=1, width=1920, height=1080)
            decision = dict(state=state,
                segments=[dict(start_boundary_id="B0", end_boundary_id="B1", evidence_frame_ids=["F0"])] if state == "KEEP" else [],
                evidence_frame_ids=[] if state == "KEEP" else ["F0"],
                reason="SYNTHETIC CPU CONTRACT ONLY; no actual visual evidence.")
            model_raw = json.dumps(decision, ensure_ascii=False, separators=(",", ":"))
            projected = teacher.boundary.canonical_response(decision, observation)
            canonical = json.dumps(projected, ensure_ascii=False, allow_nan=False, separators=(",", ":"))
            identity = dict(base_model_id=teacher.BASE_ID, model_id=teacher.TEACHER_ID,
                model_revision=teacher.TEACHER_REVISION, inference_status="PASS_REAL_TEACHER_GENERATION",
                production_test_access=False, capacity_admission_pass=True, job_source_lock_sha256="e" * 64,
                weight_files=[dict(path="SYNTHETIC_CPU_FIXTURE_ONLY/Qwen3VL-32B-Instruct-Q4_K_M.gguf",
                    sha256="5cf0136e721d6294718ec71fd8c93b17ab5dd4e2714d6079e83fa46571ad94c8"),
                    dict(path="SYNTHETIC_CPU_FIXTURE_ONLY/mmproj-Qwen3VL-32B-Instruct-F16.gguf",
                    sha256="8617824839df91f84b4840ad5084dcf50a1403a435a1f4cfc4d8c84ce6cac2fc")],
                runtime_revision=teacher.RUNTIME_REVISION, generated_utc="2026-10-08T00:00:00Z",
                prompt_sha256=teacher.text_sha(validator.prompt_for(window, observation)),
                model_raw_answer=model_raw, model_raw_answer_sha256=teacher.text_sha(model_raw), model_decision=decision,
                canonical_answer_sha256=teacher.text_sha(canonical), boundary_table_sha256=teacher.boundary.digest(teacher.boundary.tables(observation)),
                real_input_contract_sha256=observation["input_contract_sha256"], real_generation_response_sha256="f" * 64)
            record = validator.make_record(window, observation, identity, canonical)
            self.assertNotEqual(record["status"], "INVALID_TEACHER_OR_INPUT_RECEIPT", record.get("validation_errors"))
            wrong_runtime = copy.deepcopy(identity); wrong_runtime["runtime_revision"] = "SYNTHETIC_UNPINNED_RUNTIME_REJECT"
            invalid_runtime = validator.make_record(window, observation, wrong_runtime, canonical)
            self.assertEqual(invalid_runtime["status"], "INVALID_TEACHER_OR_INPUT_RECEIPT")
            self.assertIn("short decision pinned teacher/runtime differs", invalid_runtime["validation_errors"])
            digest = student.record_sha(record); records[digest] = record
            if record["sft_eligible"]:
                eligible.append(dict(teacher_record_sha256=digest))
            comparison = teacher.compare_selections(decision, decision, observation)
            prompt = teacher.review_prompt(record)
            second_teacher = copy.deepcopy(identity); second_teacher["prompt_sha256"] = teacher.text_sha(prompt)
            reviews.append(dict(schema="aic_blind_local_window_second_selection_v1", window_id=wid,
                teacher_record_sha256=digest, review_status="PASS_EXPLAINABLE_SAMPLED_WINDOW_REVIEW" if comparison["supported"] else "UNKNOWN_WEAK_SELECTION_DISAGREEMENT",
                support_class=comparison["support_class"], boundary_supported=comparison["boundary_supported"], comparison=comparison,
                reason=decision["reason"], program_complete_observation=True, same_teacher_not_independent_truth=True,
                manual_ground_truth=False, diagnostic_only=False, review_blind_to_first_answer=True,
                uncertain=not comparison["supported"], semantics_consistent=comparison["supported"],
                reviewer_model_id=teacher.TEACHER_ID, reviewer_model_revision=teacher.TEACHER_REVISION,
                reviewer_runtime_revision=second_teacher["runtime_revision"], raw_response=model_raw, raw_response_sha256=teacher.text_sha(model_raw),
                model_raw_answer=model_raw, model_raw_answer_sha256=teacher.text_sha(model_raw), model_decision=decision,
                parsed_response=decision, independent_selection=projected, second_teacher=second_teacher, review_prompt_text=prompt,
                review_prompt_sha256=teacher.text_sha(prompt), actual_observation=observation,
                server_response_sha256=second_teacher["real_generation_response_sha256"],
                source_frame_pixel_sha256=observation["frame_pixel_sha256"], source_frame_ordinals=observation["source_frame_ordinals"],
                actual_pts_sec=observation["actual_pts_sec"]))
        with tempfile.TemporaryDirectory(prefix="aic-v8-weak-receipt-") as temporary:
            raw_path = Path(temporary) / "raw_reviews.jsonl"
            raw_path.write_text("".join(json.dumps(value) + "\n" for value in reviews), encoding="utf-8")
            supported = [value["teacher_record_sha256"] for value in reviews if value["comparison"]["supported"]]
            receipt = dict(schema="aic_automated_weak_semantic_review_v2", status="PASS_AUTOMATED_WEAK_SEMANTIC_REVIEW",
                mode="AUTOMATED_WEAK_TEACHER_REVIEW_NOT_HUMAN_GROUND_TRUTH", manual_ground_truth=False,
                confirm_opened=False, contest_assets_opened=False, second_review_same_teacher_not_independent_evidence=True,
                review_blind_to_first_answer=True, no_unknown_or_unobserved_gaps_certified_negative=True, no_forced_empty_quota=True,
                validation_receipt_sha256="v" * 64, files=dict(f="hash"),
                reviewed_teacher_record_sha256=list(records), supported_teacher_record_sha256=supported,
                raw_review_receipts=dict(path=str(raw_path), sha256=student.sha(raw_path)),
                selected_denominator=3, selected_by_split=dict(train=2, dev=1),
                support_class_counts=dict(Counter(value["support_class"] for value in reviews)),
                supported_by_split=dict(train=1, dev=1), supported_positive_by_split=dict(train=1, dev=0),
                supported_explicit_empty_by_split=dict(train=0, dev=1), unknown_count=1, boundary_supported_count=1,
                perrecord_support=[dict(window_id=value["window_id"], split=records[value["teacher_record_sha256"]]["split"],
                    teacher_record_sha256=value["teacher_record_sha256"], support_class=value["support_class"],
                    boundary_supported=value["boundary_supported"], reasons=value["comparison"]["reasons"]) for value in reviews])
            result = student.verify_semantic(receipt, "v" * 64, dict(f="hash"), eligible, records, teacher, validator)
            self.assertEqual(result[1], set(supported)); self.assertEqual(result[2]["selected_denominator"], 3)
            self.assertEqual(result[2]["original_eligible_records"], 2)
            for field, value in (("unknown_count", 0), ("selected_denominator", 2),
                                 ("supported_teacher_record_sha256", list(records)),
                                 ("reviewed_teacher_record_sha256", supported)):
                changed = copy.deepcopy(receipt); changed[field] = value
                with self.assertRaises(ValueError):
                    student.verify_semantic(changed, "v" * 64, dict(f="hash"), eligible, records, teacher, validator)
            tampered = copy.deepcopy(reviews); tampered[0]["source_frame_pixel_sha256"][0] = "z" * 64
            raw_path.write_text("".join(json.dumps(value) + "\n" for value in tampered), encoding="utf-8")
            changed = copy.deepcopy(receipt); changed["raw_review_receipts"]["sha256"] = student.sha(raw_path)
            with self.assertRaisesRegex(ValueError, "identity"):
                student.verify_semantic(changed, "v" * 64, dict(f="hash"), eligible, records, teacher, validator)


if __name__ == "__main__":
    unittest.main(verbosity=2)
