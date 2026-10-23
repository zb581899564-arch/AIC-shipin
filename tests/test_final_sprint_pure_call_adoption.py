"""Real temporary JSON/source fixtures; no model, media decode or remote work."""
from copy import deepcopy
from pathlib import Path
from types import SimpleNamespace
import tempfile
import unittest

from improvement.final_sprint_v1.contracts import ref, save_new, stable_key, strict_load
from improvement.final_sprint_v1.prepare_pure_adoption import prepare_manifest, source_files
from improvement.final_sprint_v1.pure_call_adoption import OLD_COMMIT, PureCallJournal, validate_manifest


class Delegate:
    def __init__(self):
        self.calls, self.store, self.budget = [], object(), SimpleNamespace(calls=0)

    def call(self, task_id, binding, fn):
        self.calls.append((task_id, binding))
        self.budget.calls += 1
        return fn()

    def get(self, *_args):
        return None

    def has(self, *_args):
        return False

    def result_ref(self, *_args):
        raise ValueError("No fresh result")


class PureCallAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)
        self.old_dir, self.new_dir = self.root / "old_source", self.root / "new_source"
        qwen = "class QwenRuntime:\n    def __init__(self, spec):\n        self.spec = spec\n    def load(self):\n        return self.spec\n"
        for name in ("generate_images", "ground_image", "_chat", "_check_encoded", "_role"):
            qwen += "    def " + name + "(self, value):\n        return value\n"
        for name in ("_tensor_signature", "_original_base_identity", "_parameter_inventory", "_verify_files"):
            qwen += "def " + name + "(value):\n    return value\n"
        runner = "class Engine:\n" + "".join("    def " + name + "(self, value):\n        return value\n"
                                                    for name in ("query", "specialist_selection", "ground"))
        for directory in (self.old_dir, self.new_dir):
            directory.mkdir()
            for name, text in dict(qwen_runtime=qwen, runner=runner, specialist="# exact specialist\n",
                                   observation="# exact observation\n", grounding_grammar="# exact grammar\n",
                                   spatial="GROUNDING_PROMPT = 'fixed actual prompt'\n").items():
                (directory / (name + ".py")).write_text(text, encoding="utf-8")
            save_new(directory / "candidates.json", {"shared_spatial_configuration": {"context_fraction": .2}})
        model, media, clock = [save_new(self.root / (name + ".json"), {"name": name})
                               for name in ("model", "media", "clock")]
        self.old = dict(source_commit=dict(commit=OLD_COMMIT, code=dict(files=self._hashes(self.old_dir))),
                        qwen=dict(asset_tree={"files": [model]}, revision="exact"),
                        sources=[dict(media=media, clock=clock)], protected_baselines={"40.48": model},
                        baseline_parameter_receipts=[model], specialist=dict(checkpoint=model))
        self.old_ref = save_new(self.root / "old_assets.json", self.old)
        self.new = deepcopy(self.old)
        self.new["source_commit"] = dict(commit="a" * 40, code=dict(files=self._hashes(self.new_dir)))
        self.binding = dict(source=media, clock=clock, model=self.old["qwen"]["asset_tree"],
                            request=dict(prompt="fixed actual prompt", frame=7), spatial_config={"context_fraction": .2})
        self.serial = 0

    @staticmethod
    def _hashes(directory):
        return {name: value["sha256"] for name, value in source_files(directory).items()}

    def parent(self, tasks=None, **wrapper_changes):
        self.serial += 1
        directory = self.root / ("parent" + str(self.serial))
        directory.mkdir()
        owner, terminals, returned = str(self.serial) * 32, [], {}
        for task_id, binding, result, seconds, complete in tasks or [("ground_a", self.binding, {"raw_text": "ok", "gpu_seconds": 3.0}, 4.0, True)]:
            attempt = directory / task_id
            attempt.mkdir()
            binding = binding(returned) if callable(binding) else binding
            full = dict(base=dict(asset_lock=self.old_ref, code=self.old["source_commit"], no_training=True, seed=20261023),
                        call=binding, journal_schema="AIC_FINAL_CALL_V1")
            digest = stable_key(full)
            claim = save_new(attempt / "claim.json", dict(task_id=task_id, binding=full, binding_sha256=digest, owned_wrapper_id=owner))
            if complete:
                returned[task_id] = save_new(attempt / "returned_result.json", dict(schema="AIC_FINAL_CALL_V1",
                    status="FUNCTION_RETURNED_COMPLETE", task_id=task_id, binding_sha256=digest, result=result,
                    accounting=dict(wall_seconds=seconds)))
                save_new(attempt / "success.json", dict(status="SUCCESS", task_id=task_id, binding_sha256=digest,
                                                        artifacts=dict(result=returned[task_id])))
            terminal = save_new(attempt / "terminal.json", dict(task_id=task_id, claim_ref=claim, claim_sha256=claim["sha256"],
                owned_wrapper_id=owner, work_terminated=True, no_external_task_signaled=True, termination_basis="owned_wrapper_terminal"))
            terminals.append(dict(task_id=task_id, terminal_ref=terminal))
        wrapper = dict(schema="AIC_FINAL_OWNED_WRAPPER_V1", asset_lock=self.old_ref, child_exit_code=1,
            owned_wrapper_id=owner, work_terminated=True, no_external_task_signaled=True,
            stopped_owned_process=False, stop_reason=None, termination_basis="owned_wrapper_terminal", task_terminals=terminals)
        wrapper.update(wrapper_changes)
        spec = dict(old_assets=self.old_ref, wrapper=save_new(directory / "wrapper.json", wrapper), source_dir=str(self.old_dir))
        return spec, returned

    def manifest(self, parents=None):
        parents = parents or [self.parent()[0]]
        value = prepare_manifest(parents, self.new["source_commit"]["commit"], self.new_dir)
        identity = save_new(self.root / ("manifest" + str(self.serial) + ".json"), value)
        return value, identity, validate_manifest(self.new, identity)

    def test_adopts_without_inference_success_write_or_new_budget_and_deduplicates_cost(self):
        _, _, entries = self.manifest()
        delegate = Delegate()
        journal = PureCallJournal(delegate, entries)
        before = sorted(str(path) for path in self.root.rglob("*"))
        expected = strict_load(entries["ground_a"]["returned"]["path"])["result"]
        self.assertTrue(journal.has("ground_a", self.binding))
        self.assertEqual(journal.call("ground_a", self.binding, lambda: self.fail("Inference repeated")), expected)
        self.assertEqual(journal.get("ground_a", self.binding), expected)
        self.assertEqual(journal.result_ref("ground_a", self.binding), entries["ground_a"]["returned"])
        self.assertEqual((journal.historical_seconds_for_forecast, journal.adopted_ground_seconds, journal.adopted_ground_calls), (3.0, 3.0, 1))
        self.assertEqual(journal.historical_wall_seconds_for_forecast, 4.0)
        self.assertFalse(journal.historical_forecast_cold_uncertainty)
        self.assertEqual((delegate.calls, delegate.budget.calls), ([], 0))
        self.assertIs(journal.store, delegate.store)
        self.assertEqual(before, sorted(str(path) for path in self.root.rglob("*")))

    def test_unknown_tasks_forward_to_real_delegate(self):
        journal = PureCallJournal(Delegate(), self.manifest()[2])
        self.assertFalse(journal.has("ground_fresh", self.binding))
        self.assertIsNone(journal.get("ground_fresh", self.binding))
        self.assertEqual(journal.call("ground_fresh", self.binding, lambda: {"fresh": True}), {"fresh": True})
        self.assertEqual(journal.budget.calls, 1)

    def test_changed_request_prompt_native_input_or_config_is_rejected(self):
        journal = PureCallJournal(Delegate(), self.manifest()[2])
        for key, value in (("request", {"prompt": "changed"}), ("source", {"sha256": "b" * 64}), ("spatial_config", {"context_fraction": .3})):
            with self.subTest(key=key), self.assertRaisesRegex(ValueError, "request changed"):
                journal.call("ground_a", dict(self.binding, **{key: value}), lambda: self.fail("Repeated"))

    def test_packet_sha_and_new_model_or_arithmetic_profile_are_rejected(self):
        _, identity, entries = self.manifest()
        for key, value in (("revision", "different"), ("arithmetic_profile", "LOSSLESS_BF16_WEIGHTS_FP32_ARITHMETIC_V1")):
            new = deepcopy(self.new)
            new["qwen"][key] = value
            with self.assertRaises(ValueError):
                validate_manifest(new, identity)
        with Path(entries["ground_a"]["returned"]["path"]).open("a", encoding="utf-8") as stream:
            stream.write(" ")
        with self.assertRaisesRegex(ValueError, "SHA256|byte count|inventory differs|packet identity differs"):
            validate_manifest(self.new, identity)

    def test_old_source_sha_changed_or_new_producer_body_changed_is_rejected(self):
        parent = self.parent()[0]
        path = self.old_dir / "specialist.py"
        path.write_text("# altered old source\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "source_commit.code.files"):
            prepare_manifest([parent], "a" * 40, self.new_dir)

    def test_new_producer_and_default_load_ast_change_are_rejected(self):
        parent = self.parent()[0]
        path = self.new_dir / "qwen_runtime.py"
        original = path.read_text(encoding="utf-8")
        for replacement in (original.replace("def _chat(self, value):\n        return value", "def _chat(self, value):\n        return 'changed'"),
                            original.replace("def load(self):\n        return self.spec", "def load(self):\n        self.spec = {}\n        return self.spec")):
            path.write_text(replacement, encoding="utf-8")
            with self.assertRaisesRegex(ValueError, "producer AST|BF16 loader"):
                prepare_manifest([parent], "a" * 40, self.new_dir)

    def test_source_phase_and_incomplete_calls_are_excluded(self):
        tasks = [(name, self.binding, {"output": name}, 1.0, complete) for name, complete in
                 (("ground_a", True), ("source_g_subject_0", True), ("phase_0_clip0", True), ("query_incomplete", False))]
        value, _, entries = self.manifest([self.parent(tasks)[0]])
        self.assertEqual(set(entries), {"ground_a"})
        self.assertEqual({row["task_id"] for row in value["excluded"]}, {"source_g_subject_0", "phase_0_clip0", "query_incomplete"})

    def test_nested_features_ref_keeps_old_packet_identity(self):
        tasks = [("clip_features_0", self.binding, {"features": [1, 2]}, 8.0, True),
                 ("specialist_source_0", lambda refs: dict(self.binding, features_ref=refs["clip_features_0"]),
                  {"selected_frames": [7]}, 2.0, True)]
        parent, old_refs = self.parent(tasks)
        journal = PureCallJournal(Delegate(), self.manifest([parent])[2])
        feature_ref = journal.result_ref("clip_features_0", self.binding)
        self.assertEqual(feature_ref, old_refs["clip_features_0"])
        binding = dict(self.binding, features_ref=feature_ref)
        self.assertEqual(journal.call("specialist_source_0", binding, lambda: self.fail("Repeated")), {"selected_frames": [7]})
        self.assertEqual(journal.historical_seconds_for_forecast, 2.0)
        self.assertTrue(journal.historical_forecast_cold_uncertainty)
        self.assertEqual(journal.historical_forecast_cold_tasks, ["specialist_source_0"])

    def test_identical_duplicate_semantics_pin_first_parent_and_keep_original_cost(self):
        first, refs = self.parent()
        second = self.parent([("ground_a", self.binding, {"raw_text": "ok", "gpu_seconds": 9.0}, 10.0, True)])[0]
        entries = self.manifest([first, second])[2]
        self.assertEqual(entries["ground_a"]["returned"], refs["ground_a"])
        self.assertEqual(entries["ground_a"]["historical_wall_seconds"], 4.0)

    def test_duplicate_conflicting_semantic_output_or_binding_fails(self):
        first = self.parent()[0]
        for binding, result in ((self.binding, {"raw_text": "different"}), (dict(self.binding, request={"prompt": "different"}), {"raw_text": "ok"})):
            second = self.parent([("ground_a", binding, result, 2.0, True)])[0]
            with self.assertRaisesRegex(ValueError, "Duplicate task"):
                prepare_manifest([first, second], "a" * 40, self.new_dir)

    def test_stopped_or_foreign_wrapper_and_changed_prompt_cannot_adopt(self):
        with self.assertRaisesRegex(ValueError, "naturally terminated"):
            prepare_manifest([self.parent(stopped_owned_process=True)[0]], "a" * 40, self.new_dir)
        with self.assertRaisesRegex(ValueError, "owned-wrapper identity"):
            prepare_manifest([self.parent(owned_wrapper_id="foreign")[0]], "a" * 40, self.new_dir)
        (self.new_dir / "spatial.py").write_text("GROUNDING_PROMPT = 'changed'\n", encoding="utf-8")
        with self.assertRaisesRegex(ValueError, "prompt/shared spatial"):
            prepare_manifest([self.parent()[0]], "a" * 40, self.new_dir)


if __name__ == "__main__":
    unittest.main()
