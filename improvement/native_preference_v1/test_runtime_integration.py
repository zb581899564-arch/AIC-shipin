"""Execute the real pilot orchestration against explicit synthetic I/O boundaries.

These are CPU standard-library workflow tests.  The fake runtime does not load
Torch/Qwen and its counters are simulated; passing this suite is NOT the Torch
CPU gate, a GPU execution receipt, or evidence of predictive improvement.
"""
from __future__ import annotations

from contextlib import ExitStack
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from improvement.bottleneck_24h_v1 import summary_grammar6
from . import run, runtime
from .contracts import StageBudget, digest, reference, save_new, strict_load


class Tokenizer:
    eos_token_id = 999

    def get_vocab(self):
        return {chr(value): value for value in range(32, 127)}

    def convert_tokens_to_ids(self, text):
        return 999 if text == "<|im_end|>" else None

    def decode(self, ids, **_):
        return "".join("<|im_end|>" if value == 999 else chr(value) for value in ids)


class Prefix:
    shape = (1, 3)

    def __init__(self, uid):
        self.uid = uid


class PilotFixture:
    def __init__(self, path):
        self.path, self.trace, self.instances, self.stores = path, [], [], []
        self.fail_reference_uid = self.drift_uid = None
        self.data = {}
        pairs, signatures = {"train": [], "check": []}, {}
        for scope in ("train", "check"):
            requests, request_refs, sources, clocks, values = {}, {}, {}, {}, {}
            for source_number in range(8):
                sid = scope + "_source_" + str(source_number)
                windows = 4 if scope == "train" else (6 if source_number < 3 else 5)
                clock = dict(normalized_exact_pts=[str(value) for value in range(2 * windows)],
                             physical_end_exact=str(2 * windows))
                clock_ref = save_new(path / (sid + "_clock.json"), clock)
                clocks[sid] = clock
                sources[sid] = dict(clock_ref=clock_ref)
                for window in range(windows):
                    uid = sid + "/window_" + str(window)
                    signature = {name: dict(shape=[1, 3], dtype="synthetic", sha256=run.stable_key(name, uid))
                                 for name in runtime.INPUT_KEYS}
                    request = dict(uid=uid, sid=sid, input_signature=signature,
                                   plan=dict(window_start_exact=str(2 * window), window_end_exact=str(2 * window + 2)))
                    requests[uid] = request
                    request_refs[uid] = save_new(path / (sid + "_window_" + str(window) + ".json"), request)
                    values[uid] = dict(input_ids=Prefix(uid), attention_mask=object(),
                                       pixel_values_videos=object(), video_grid_thw=object())
                    signatures[scope + ":" + uid] = signature
                    if scope == "train" or window < 2:
                        chosen, rejected = '{"segments":[[0,1]]}', '{"segments":[[1,2]]}'
                        pairs[scope].append(dict(pair_id=scope + ":" + uid, scope=scope, source_id=sid,
                            uid=uid, input_key=scope + ":" + uid, token_length_equality_checked=True,
                            equal_native_budget=True, budget=1, chosen_selected=[2 * window],
                            rejected_selected=[2 * window + 1], chosen_answer=chosen, rejected_answer=rejected,
                            chosen_ids=[ord(c) for c in chosen] + [999], rejected_ids=[ord(c) for c in rejected] + [999]))
            self.data[scope] = dict(requests=requests, request_refs=request_refs, sources=sources,
                                    clocks=clocks, values=values)
        self.config = strict_load(Path(__file__).with_name("config.example.json"))
        self.config.update(run_id="synthetic_pilot", run_root=str(path / "synthetic_pilot"))
        config_ref = save_new(path / "config.json", self.config)
        assets_ref = save_new(path / "assets.json", dict(synthetic_unit_test_only=True))
        self.binding = dict(config_ref=config_ref, asset_manifest_ref=assets_ref,
                            code_identity=dict(synthetic_unit_test_only=True))
        self.manifest = dict(workspace_root=str(path), model_spec=dict(synthetic_unit_test_only=True))
        prepared = dict(status=run.PREPARED_STATUS, **self.binding,
                        train_pairs=pairs["train"], check_pairs=pairs["check"],
                        train_sources=list(self.data["train"]["sources"]), check_sources=list(self.data["check"]["sources"]),
                        check_case_ids=list(self.data["check"]["requests"]), case_signatures=signatures)
        self.prepared_ref = save_new(path / "prepared.json", prepared)
        self.checks_ref = save_new(path / "synthetic_boundary.json", dict(
            synthetic_unit_test_only=True, actual_torch_gate="NOT_RUN"))
        self.directory = path / "pilot"
        self.directory.mkdir()
        self.budget = StageBudget(path, 60, 10 << 20, 66_000)
        self.args = SimpleNamespace(prepared=self.prepared_ref["path"], torch_checks=self.checks_ref["path"])

    def store_factory(self, _manifest, scope):
        fixture, data = self, self.data[scope]

        class Store:
            def __init__(self):
                self.workspace = fixture.path
                self.scope = scope
                self.requests, self.request_refs = data["requests"], data["request_refs"]
                self.sources, self.clocks = data["sources"], data["clocks"]
                self.source_ids, self.case_ids = tuple(self.sources), tuple(self.requests)
                self.close_calls = 0

            def case(self, uid):
                request = self.requests[uid]
                if uid == fixture.drift_uid:
                    request = dict(request, input_signature=dict(changed_after_prepare=True))
                return request, data["values"][uid], self.clocks[request["sid"]]

            def close(self):
                self.close_calls += 1

        store = Store()
        self.stores.append(store)
        return store

    def runtime_factory(self, _spec, check_budget, on_event, *, seed):
        fixture = self
        assert seed == 20261019

        class FakeRuntime:
            def __init__(self):
                self.tokenizer, self.eos, self.state = Tokenizer(), 999, "unloaded"
                self.torch = SimpleNamespace(cuda=SimpleNamespace(max_memory_allocated=lambda: 0,
                                                                 max_memory_reserved=lambda: 0))
                self.counts = {key: 0 for key in ("sequence_score_calls", "sequence_scores_completed",
                    "generation_calls", "generations_completed", "top_level_forward_calls", "backward_calls",
                    "backwards_completed", "optimizer_steps")}

            def forward(self, number):
                for _ in range(number):
                    check_budget(forward=True)
                    self.counts["top_level_forward_calls"] += 1

            def teacher_scores(self, number):
                self.forward(number)
                self.counts["sequence_score_calls"] += number
                self.counts["sequence_scores_completed"] += number

            def load(self):
                fixture.trace.append(("load",))
                self.state = "reference"
                return self.identity()

            def identity(self):
                return dict(synthetic_unit_test_only=True, eos_token_id=999)

            def tokenize_answer(self, _values, answer):
                return [ord(char) for char in answer] + [999]

            def cache_reference(self, pairs, get_input):
                assert self.state == "reference" and len(pairs) == 48
                assert self.counts["generation_calls"] == 0
                fixture.trace.append(("cache_reference_begin",))
                entries = {}
                for pair in pairs:
                    assert set(get_input(pair["input_key"])) == runtime.INPUT_KEYS
                    self.teacher_scores(2)
                    entries[pair["pair_id"]] = dict(chosen_logprob=-10., rejected_logprob=-12.)
                fixture.trace.append(("cache_reference_complete", len(entries)))
                return dict(entries=entries, synthetic_unit_test_only=True)

            def generate(self, values, _constraint):
                assert self.state in ("reference", "policy_reloaded"), "Policy must reload before any generation"
                uid = values["input_ids"].uid
                role = "reference" if self.state == "reference" else "policy"
                fixture.trace.append(("generate", role, uid))
                self.counts["generation_calls"] += 1
                self.forward(1)
                if role == "reference" and uid == fixture.fail_reference_uid:
                    on_event("generation_raw", dict(raw_text='{"segments":[', ids=[123], synthetic_unit_test_only=True))
                    raise ValueError("Synthetic incomplete EOS generation")
                text = '{"segments":[]}'
                self.counts["generations_completed"] += 1
                return dict(text=text, ids=[ord(c) for c in text] + [999], eos=True, eos_token_id=999,
                            actual_model_call=True, input_signature=fixture.data["check"]["requests"][uid]["input_signature"])

            def train_pairs(self, pairs, get_input, cache, *, updates, grad_accum, lr, beta):
                assert self.state == "reference" and (updates, grad_accum, lr, beta) == (16, 2, 1e-5, .1)
                assert len(pairs) == 32 and all(pair["scope"] == "train" for pair in pairs)
                assert self.counts["generations_completed"] == 43 and len(cache["entries"]) == 48
                fixture.trace.append(("train", tuple(pair["pair_id"] for pair in pairs)))
                for pair in pairs:
                    get_input(pair["input_key"])
                self.teacher_scores(2 + 4 * len(pairs))
                self.counts.update(backward_calls=64, backwards_completed=64, optimizer_steps=16)
                self.state = "trained"
                return dict(synthetic_unit_test_only=True, completed_updates=16)

            def save_policy(self, directory):
                assert self.state == "trained"
                fixture.trace.append(("save",))
                path = Path(directory)
                path.mkdir()
                weights = path / "adapter_model.safetensors"
                weights.write_bytes(b"SYNTHETIC UNIT TEST ONLY - NOT MODEL WEIGHTS")
                config_ref = save_new(path / "adapter_config.json", dict(synthetic_unit_test_only=True))
                return dict(directory=str(path), adapter_weights=reference(weights), adapter_config=config_ref,
                            runtime=self.identity())

            def load_policy(self, directory, expected_sha256):
                assert self.state == "trained"
                assert digest(Path(directory) / "adapter_model.safetensors") == expected_sha256
                fixture.trace.append(("reload",))
                self.state = "policy_reloaded"

            def score(self, _values, _suffix):
                assert self.state == "policy_reloaded", "Heldout policy must be the actual reloaded checkpoint"
                fixture.trace.append(("score_reloaded",))
                self.teacher_scores(1)
                return -9.

            def verify_final(self):
                assert self.state == "policy_reloaded"
                fixture.trace.append(("verify_reloaded",))
                return dict(synthetic_unit_test_only=True)

        instance = FakeRuntime()
        fixture.instances.append(instance)
        return instance

    def invoke(self):
        with ExitStack() as patches:
            patches.enter_context(patch.object(run, "NativeInputStore", self.store_factory))
            patches.enter_context(patch.object(runtime, "QwenPreferenceRuntime", self.runtime_factory))
            patches.enter_context(patch.object(run, "torch_gate", return_value=self.checks_ref))
            patches.enter_context(patch.object(run, "grammar_module", return_value=summary_grammar6))
            return run.pilot(self.config, self.manifest, self.binding, self.directory, self.budget, args=self.args)


class RuntimeIntegrationChecks(unittest.TestCase):
    def test_real_pilot_order_complete_sources_and_final_reload(self):
        with tempfile.TemporaryDirectory(prefix="aic_pilot_flow_") as directory:
            fixture = PilotFixture(Path(directory))
            receipt = strict_load(fixture.invoke()["path"])
            trace = fixture.trace
            cache_index = next(i for i, value in enumerate(trace) if value[0] == "cache_reference_complete")
            train_index = next(i for i, value in enumerate(trace) if value[0] == "train")
            save_index = trace.index(("save",))
            reload_index = trace.index(("reload",))
            self.assertEqual(trace[cache_index][1], 48)
            reference_calls = [(i, value[2]) for i, value in enumerate(trace) if value[:2] == ("generate", "reference")]
            policy_calls = [(i, value[2]) for i, value in enumerate(trace) if value[:2] == ("generate", "policy")]
            expected = set(fixture.data["check"]["requests"])
            self.assertEqual(len(expected), 43)
            self.assertEqual({uid for _, uid in reference_calls}, expected)
            self.assertEqual({uid for _, uid in policy_calls}, expected)
            self.assertEqual(len(reference_calls), 43)
            self.assertEqual(len(policy_calls), 43)
            self.assertTrue(all(cache_index < index < train_index for index, _ in reference_calls))
            self.assertLess(train_index, save_index)
            self.assertLess(save_index, reload_index)
            self.assertTrue(all(index > reload_index for index, _ in policy_calls))
            self.assertTrue(all(index > reload_index for index, value in enumerate(trace) if value[0] == "score_reloaded"))
            self.assertEqual(receipt["status"], run.PILOT_STATUS)
            self.assertTrue(receipt["no_automatic_production"])
            self.assertEqual(receipt["counts"]["sequence_score_calls"], 258)
            self.assertEqual(receipt["counts"]["sequence_scores_completed"], 258)
            self.assertEqual(receipt["counts"]["generation_calls"], 86)
            self.assertEqual(receipt["counts"]["backwards_completed"], 64)
            self.assertEqual(receipt["counts"]["optimizer_steps"], 16)
            self.assertEqual(receipt["counts"]["top_level_forward_calls"], fixture.budget.forward_count)
            self.assertEqual(len(fixture.instances), 1, "The orchestration must use one runtime, not separate roles")

    def test_reference_failure_is_persisted_and_training_never_starts(self):
        with tempfile.TemporaryDirectory(prefix="aic_pilot_failure_") as directory:
            fixture = PilotFixture(Path(directory))
            fixture.fail_reference_uid = list(fixture.data["check"]["requests"])[12]
            with self.assertRaisesRegex(ValueError, "Synthetic incomplete EOS"):
                fixture.invoke()
            failure = strict_load(fixture.directory / "reference_0012.json")
            self.assertEqual(failure["status"], "FAILED")
            self.assertFalse(failure["failed_output_to_empty"])
            self.assertNotIn("selected_ordinals", failure)
            self.assertNotIn("legal_empty", failure)
            self.assertFalse(any(value[0] in ("train", "save", "reload") for value in fixture.trace))
            self.assertFalse((fixture.directory / "completion.json").exists())
            journal = [json.loads(line) for line in (fixture.directory / "events.jsonl").read_text().splitlines()]
            self.assertEqual(journal[-1]["raw_text"], '{"segments":[')
            self.assertTrue(all(store.close_calls > 0 for store in fixture.stores))

    def test_prepared_visual_input_drift_stops_before_reference_forward(self):
        with tempfile.TemporaryDirectory(prefix="aic_pilot_input_binding_") as directory:
            fixture = PilotFixture(Path(directory))
            fixture.drift_uid = next(iter(fixture.data["train"]["requests"]))
            with self.assertRaisesRegex(ValueError, "Prepared input changed"):
                fixture.invoke()
            self.assertEqual(fixture.instances[0].counts["top_level_forward_calls"], 0)
            self.assertFalse(any(value[0] in ("cache_reference_begin", "train", "save", "reload") for value in fixture.trace))
            self.assertFalse((fixture.directory / "completion.json").exists())

    def test_changed_production_runtime_stops_before_policy_load_or_generation(self):
        with tempfile.TemporaryDirectory(prefix="aic_production_identity_") as directory:
            fixture = PilotFixture(Path(directory))
            pilot_ref = fixture.invoke()
            completed = run.load_pilot(pilot_ref["path"], fixture.prepared_ref, fixture.binding)
            review_ref = save_new(fixture.path / "synthetic_review_boundary.json", dict(
                schema="AIC_NATIVE_PREFERENCE_REVIEW_V1", status="ELIGIBLE_FOR_EXECUTION_REVIEW",
                **fixture.binding, synthetic_unit_test_only=True, pilot_completion_ref=pilot_ref,
                prepared_ref=fixture.prepared_ref, final_adapter_ref=completed["final_adapter_ref"]))
            admission_ref = save_new(fixture.path / "synthetic_admission_boundary.json",
                                     dict(synthetic_unit_test_only=True, actual_execution_admission=False))
            formal = dict(fixture.manifest, _asset_manifest_ref=fixture.binding["asset_manifest_ref"])
            args = SimpleNamespace(**vars(fixture.args), pilot=pilot_ref["path"], review=review_ref["path"],
                admission=admission_ref["path"], assets=fixture.binding["asset_manifest_ref"]["path"], production_assets=None)
            destination = fixture.path / "production"
            destination.mkdir()
            before = len(fixture.trace)

            def changed_runtime(*args, **kwargs):
                actual = fixture.runtime_factory(*args, **kwargs)
                actual.identity = lambda: dict(synthetic_unit_test_only=True, eos_token_id=999,
                                                versions=dict(torch="DIFFERENT_SYNTHETIC_ENVIRONMENT"))
                return actual

            # Asset/admission boundaries are synthetic here; the real production
            # function, completed-pilot binding and runtime identity gate execute.
            with ExitStack() as patches:
                patches.enter_context(patch.object(run, "NativeInputStore",
                                                    lambda manifest, scope: fixture.store_factory(manifest, "check")))
                patches.enter_context(patch.object(runtime, "QwenPreferenceRuntime", changed_runtime))
                patches.enter_context(patch.object(run, "torch_gate", return_value=fixture.checks_ref))
                patches.enter_context(patch.object(run.asset_api, "load_assets", return_value=formal))
                patches.enter_context(patch.object(run.asset_api, "preflight_assets", return_value=None))
                patches.enter_context(patch.object(run, "require_production_assets", return_value=None))
                patches.enter_context(patch.object(run, "validate_admission", return_value=None))
                with self.assertRaisesRegex(ValueError, "production runtime differs"):
                    run.production(fixture.config, fixture.manifest, fixture.binding, destination,
                                   fixture.budget, args=args)
            self.assertEqual(fixture.trace[before:], [("load",)])
            self.assertEqual(fixture.instances[-1].counts["top_level_forward_calls"], 0)
            self.assertEqual(fixture.instances[-1].counts["optimizer_steps"], 0)
            self.assertFalse((destination / "completion.json").exists())


if __name__ == "__main__":
    unittest.main()
