"""Synthetic metadata only: original phase success is never executed/re-QA'd."""
from copy import deepcopy
import json
from pathlib import Path
import tempfile
import unittest

from improvement.final_sprint_v1.contracts import ref, save_new, stable_key, strict_load
from improvement.final_sprint_v1.observation import plan_clips
from improvement.final_sprint_v1.phase_call_adoption import (
    AMENDMENT_STATE, BASE_PARAMETERS, BASE_SHA, PARENT_COMMIT, PHASE_METHODS, PROFILE,
    PhaseCallJournal, prepare_manifest, validate_manifest)
from improvement.final_sprint_v1.prepare_pure_adoption import source_files
from improvement.final_sprint_v1.pure_call_adoption import PureCallJournal
from tests.test_final_sprint_pure_call_adoption import Delegate


class PhaseAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.old_dir, self.new_dir = self.root / "old_source", self.root / "new_source"
        self.old_run = self.root / "original_fp32_run"
        (self.old_run / "model_parameters").mkdir(parents=True)
        self.config = dict(clip_seconds=8, samples_per_clip=32, duration_fraction="1/4",
                           phase_policy="event", arithmetic_profile=PROFILE)
        candidate = dict(configuration=self.config, selection="phase_event")
        for directory in (self.old_dir, self.new_dir):
            directory.mkdir()
            qwen = "class QwenRuntime:\n" + "".join("    def " + name + "(self):\n        return None\n" for name in PHASE_METHODS)
            (directory / "qwen_runtime.py").write_text(qwen, encoding="utf-8")
            (directory / "runner.py").write_text("class Engine:\n    def phases(self):\n        return None\ndef phase_options(value):\n    return value\n", encoding="utf-8")
            for name in ("numeric_precision.py", "observation.py", "temporal.py"):
                (directory / name).write_text("# identical dependency\n", encoding="utf-8")
            temporal = deepcopy(candidate)
            temporal["configuration"]["spatial_policy"] = "FROZEN_EXISTING_SOURCE_FIELD"
            save_new(directory / "candidates.json", {"candidates": {"r_phase_event": candidate, "r_time_event": temporal}})
        self.weight = save_new(self.root / "synthetic_weight_identity.json", {"fixture": "no actual model"})
        media = save_new(self.root / "synthetic_media_identity.json", {"fixture": "no actual media"})
        clock = save_new(self.root / "clock.json", dict(source_sha256=media["sha256"], normalized_exact_pts=["0", "1", "2", "3"], physical_end_exact="4"))
        self.source = dict(video_id="413", media=media, clock=clock, n_frames=4, width=16, height=16)
        self.plans = plan_clips(dict(self.source, normalized_exact_pts=["0", "1", "2", "3"], physical_end_exact="4"))
        self.old = dict(source_commit=dict(commit=PARENT_COMMIT, code=dict(files=self.hashes(self.old_dir))),
                        run_root=str(self.old_run), qwen=dict(asset_tree={"files": [self.weight]}, revision="fixed"),
                        sources=[self.source], protected_baselines={}, baseline_parameter_receipts=[])
        conversion = dict(schema="AIC_LOSSLESS_FP32_ARITHMETIC_PROOF_V1", arithmetic_profile=PROFILE,
            source_parameter_dtype="torch.bfloat16", materialized_parameter_dtype="torch.float32",
            roundtrip_BASE_identity=dict(sha256=BASE_SHA, parameters=BASE_PARAMETERS), training_updates=0,
            backend=dict(cuda_autocast_enabled=False, cuda_matmul_allow_tf32=False, cudnn_allow_tf32=False, float32_matmul_precision="highest"))
        conversion.update({key: True for key in ("exact_original_values_preserved", "all_tensors_frozen",
            "original_BF16_identity_verified_before_conversion", "tensor_objects_aliases_shapes_counts_unchanged", "inference_autocast_disabled")})
        self.parameters = dict(schema="AIC_FINAL_PARAMETERS_V1", origin="actual_loaded", component_id="qwen_base",
            total_elements=BASE_PARAMETERS, quantization_does_not_reduce_parameters=True, weight_files=[self.weight],
            tensors=[dict(name="fixture", aliases=["fixture"], shape=[BASE_PARAMETERS], elements=BASE_PARAMETERS,
                          source=dict(weight_sha256=self.weight["sha256"], tensor_name="fixture"))],
            loading_proof=dict(local_only=True, strict_BASE_loading_info_checked=True, all_runtime_parameter_keys_bound=True,
                optional_TIME_loaded=False, revision="fixed", arithmetic_conversion=conversion,
                original_base_identity=dict(verified_before_adapter=True, sha256=BASE_SHA, expected_sha256=BASE_SHA, parameters=BASE_PARAMETERS)))

    @staticmethod
    def hashes(directory):
        return {name: item["sha256"] for name, item in source_files(directory).items()}

    def fixtures(self, *, wrong_owner=False, bad_stop=False, failed_smoke=False):
        old_ref = save_new(self.root / "old_assets.json", self.old)
        parameter_ref = save_new(self.old_run / "model_parameters/qwen_base.json", self.parameters)
        self.new = deepcopy(self.old)
        self.new["source_commit"] = dict(commit="a" * 40, code=dict(files=self.hashes(self.new_dir)))
        parents, outputs = [], []
        smoke_path = self.old_run / "smoke.json"
        for index, action in enumerate(("smoke", "run")):
            directory = self.old_run / ("wrapper_" + action)
            directory.mkdir()
            owner, pid = action * 8, 42 + index
            argv = ["python", "-m", "improvement.final_sprint_v1.cli", action, "--assets", old_ref["path"],
                    "--expected-commit", PARENT_COMMIT, "--candidate", "r_phase_event"]
            save_new(directory / "claim.json", dict(wrapper_id=owner, asset_lock=old_ref, child_pid=pid, command=argv))
            plan = self.plans[index]
            task = "phase_413_" + plan["clip_id"]
            binding = dict(source=self.source["media"], clock=self.source["clock"], clip=plan,
                           model=self.old["qwen"]["asset_tree"], algorithm="NATIVE_ACTION_PHASE_SEMANTIC_WORDS_V2")
            full = dict(base=dict(asset_lock=old_ref, code=self.old["source_commit"], no_training=True, seed=20261023),
                        call=binding, journal_schema="AIC_FINAL_CALL_V1")
            attempt = directory / task
            attempt.mkdir()
            claim = save_new(attempt / "claim.json", dict(task_id=task, binding=full, binding_sha256=stable_key(full), owned_wrapper_id=owner, pid=pid))
            alternatives = [dict(phase=phase, token_ids=[index + 1, 5], token_log_probabilities=[-.5, -.1])
                            for index, phase in enumerate(("ordinary", "setup", "apex", "resolution"))]
            result = dict(status="MODEL_OK", clip=plan, role="base", parameter_count=BASE_PARAMETERS, no_global_source_prefix=True, training_updates=0,
                phases=[dict(cell=cell, phase="setup", alternatives=alternatives) for cell in plan["cells"]], raw_text="setup\n", gpu_seconds=.25,
                score_definition="MEAN_COMPLETE_SEMANTIC_WORD_AND_LF_FULL_VOCAB_LOGPROB",
                input_proof=dict(physical_source_sha256=self.source["media"]["sha256"], pixel_sha256=["a" * 64],
                                 input_identity={"sha256": "b" * 64}, local_input=dict(source_id="413", source_sha256=self.source["media"]["sha256"],
                                     pixel_sha256=["a" * 64], native_ordinals=plan["sample_ordinals"], sample_pts_exact=plan["sample_pts_exact"])),
                independent_reference_forwards=4 if action == "smoke" else 0,
                independent_unpadded_reference_checks=[dict(status="PASS_CACHED_VS_UNPADDED_REFERENCE", token_absolute_tolerance=.20,
                    mean_score_absolute_tolerance=.08, no_reference_substitution=True)] if action == "smoke" else [])
            returned = save_new(attempt / "returned_result.json", dict(schema="AIC_FINAL_CALL_V1", status="FUNCTION_RETURNED_COMPLETE",
                task_id=task, binding_sha256=stable_key(full), result=result, accounting=dict(wall_seconds=1.0)))
            save_new(attempt / "success.json", dict(status="SUCCESS", task_id=task, binding_sha256=stable_key(full), artifacts=dict(result=returned)))
            proof = save_new(attempt / "terminal.json", dict(task_id=task, claim_ref=claim, claim_sha256=claim["sha256"], owned_wrapper_id=owner,
                work_terminated=True, no_external_task_signaled=True, termination_basis="owned_wrapper_terminal"))
            terminal = dict(schema="AIC_FINAL_OWNED_WRAPPER_V1", asset_lock=old_ref, owned_wrapper_id=owner,
                work_terminated=True, no_external_task_signaled=True, termination_basis="owned_wrapper_terminal",
                stopped_owned_process=action == "run", stop_reason="OwnedWrapperStop" if action == "run" else None,
                child_exit_code=(-15 if not bad_stop else -9) if action == "run" else (1 if failed_smoke else 0),
                task_terminals=[dict(task_id=task, terminal_ref=proof), dict(task_id="ground_excluded")])
            wrapper = save_new(directory / "completion.json", terminal)
            if action == "smoke":
                save_new(smoke_path, dict(status="REAL_ENGINEERING_SMOKE_PASS", binding=dict(asset_lock=old_ref, code=self.old["source_commit"], family="phase"),
                    parameter_receipts=[parameter_ref], phase_reference_forwards=4, phase_clips=1, evidence_refs=[returned]))
            spec = dict(old_assets=old_ref, wrapper=wrapper, source_dir=str(self.old_dir), parameter_receipt=parameter_ref, smoke_receipt=ref(smoke_path))
            if action == "run":
                supervisor = ["python", "-m", "improvement.final_sprint_v1.supervise", "--action", "run", "--assets", old_ref["path"],
                              "--expected-commit", PARENT_COMMIT, "--candidate", "r_phase_event"]
                spec["route_amendment"] = save_new(self.root / "amendment.json", dict(state=AMENDMENT_STATE, wrapper=str(directory),
                    wrapper_id=owner, owned_child=pid + 1 if wrong_owner else pid, no_external_signal=True,
                    do_not_repeat_successful_calls=True, supervisor_argv=supervisor))
            parents.append(spec)
            outputs.append((task, binding, returned))
        return parents, outputs

    def adopt(self, parents):
        manifest = prepare_manifest(parents, "a" * 40, "r_time_event", self.new_dir)
        identity = save_new(self.root / "phase_adoption.json", manifest)
        return manifest, validate_manifest(self.new, identity)

    def test_natural_smoke_and_owned_route_stop_adopt_old_packets_without_model_or_cost(self):
        parents, outputs = self.fixtures()
        manifest, entries = self.adopt(parents)
        self.assertEqual(len(entries), 2)
        self.assertEqual({row["reason"] for row in manifest["excluded"]}, {"NOT_PHASE"})
        journal = PhaseCallJournal(Delegate(), entries)
        for task, binding, returned in outputs:
            self.assertIsNotNone(journal.call(task, binding, lambda: self.fail("Successful phase repeated")))
            self.assertEqual(journal.result_ref(task, binding), returned)
        self.assertEqual(journal.historical_seconds_for_forecast, .5)
        self.assertEqual(journal.budget.calls, 0)
        with self.assertRaisesRegex(ValueError, "request changed"):
            PureCallJournal(Delegate(), entries).get(outputs[0][0], outputs[0][1])

    def test_changed_phase_request_and_bf16_entries_cannot_cross_into_fp32_adapter(self):
        parents, outputs = self.fixtures()
        _, entries = self.adopt(parents)
        journal = PhaseCallJournal(Delegate(), entries)
        task, binding, _ = outputs[0]
        with self.assertRaisesRegex(ValueError, "source/native clip"):
            journal.get(task, dict(binding, algorithm="different"))
        entries[task]["validated_arithmetic_profile"] = "BF16"
        with self.assertRaisesRegex(ValueError, "FP32-only"):
            PhaseCallJournal(Delegate(), entries)

    def test_roundtrip_change_rejects_old_evidence(self):
        self.parameters["loading_proof"]["arithmetic_conversion"]["roundtrip_BASE_identity"]["sha256"] = "b" * 64
        parents, _ = self.fixtures()
        with self.assertRaisesRegex(ValueError, "roundtrip proof"):
            self.adopt(parents)

    def test_wrong_owned_child_cannot_authorize_stopped_run(self):
        parents, _ = self.fixtures(wrong_owner=True)
        with self.assertRaisesRegex(ValueError, "owned stop"):
            self.adopt(parents)

    def test_other_signal_is_not_adoption_authority(self):
        parents, _ = self.fixtures(bad_stop=True)
        with self.assertRaisesRegex(ValueError, "owned stop"):
            self.adopt(parents)

    def test_failed_natural_smoke_is_rejected(self):
        parents, _ = self.fixtures(failed_smoke=True)
        with self.assertRaisesRegex(ValueError, "complete naturally"):
            self.adopt(parents)

    def test_changed_qwen_helper_rejected(self):
        parents, _ = self.fixtures()
        path = self.new_dir / "qwen_runtime.py"
        path.write_text(path.read_text(encoding="utf-8").replace("return None", "return False", 1), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "helper AST changed"):
            self.adopt(parents)

    def test_missing_natural_smoke_parent_is_rejected_even_with_old_pass_receipt(self):
        parents, _ = self.fixtures()
        with self.assertRaisesRegex(ValueError, "naturally passed FP32 smoke"):
            self.adopt(parents[1:])

    def test_arithmetic_backend_tf32_is_rejected(self):
        self.parameters["loading_proof"]["arithmetic_conversion"]["backend"]["cuda_matmul_allow_tf32"] = True
        parents, _ = self.fixtures()
        with self.assertRaisesRegex(ValueError, "arithmetic/roundtrip proof"):
            self.adopt(parents)

    def test_changed_new_phase_configuration_rejected(self):
        parents, _ = self.fixtures()
        path = self.new_dir / "candidates.json"
        registry = strict_load(path)
        registry["candidates"]["r_time_event"] = deepcopy(registry["candidates"]["r_time_event"])
        registry["candidates"]["r_time_event"]["configuration"]["samples_per_clip"] = 16
        path.write_text(json.dumps(registry), encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "temporal/arithmetic options"):
            self.adopt(parents)

    def test_arbitrary_parent_implementation_is_rejected(self):
        self.old["source_commit"]["commit"] = "b" * 40
        parents, _ = self.fixtures()
        with self.assertRaisesRegex(ValueError, "original083d"):
            self.adopt(parents)


if __name__ == "__main__":
    unittest.main()
