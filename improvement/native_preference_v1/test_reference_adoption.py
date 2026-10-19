"""Synthetic retained-reference adoption; no Torch/model/tensor loading."""
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest

from improvement.bottleneck_24h_v1 import summary_grammar6
from .contracts import reference, strict_load
from .reference_adoption import adopt_reference
from .test_runtime_integration import PilotFixture, Tokenizer


class OriginFixture(PilotFixture):
    def __init__(self, path):
        super().__init__(path)
        self.base = dict(sha256="74bcce81cfcb0893cf4b4c25ae36ec908d6ea669583aedd0f3940063080b8b59",
                         parameters=8767123696)
        weights = path / "original_TIME.safetensors"
        weights.write_bytes(b"synthetic original weights; never loaded")
        self.manifest["model_spec"].update(adapter_weights=reference(weights), base_sha256=self.base["sha256"])
        gate = self.write("accepted_check.json", dict(synthetic=True))
        self.manifest["scopes"] = dict(check=dict(input_acceptance_ref=gate))
        outputs, details = [], []
        for i, (uid, request) in enumerate(self.data["check"]["requests"].items()):
            text = '{"segments":[]}'
            common = dict(uid=uid, sid=request["sid"], request_ref=self.data["check"]["request_refs"][uid],
                generated_ids=[ord(c) for c in text] + [999], model_role="INIT_TIME",
                model_weights_ref=reference(weights))
            token = self.write("old_tokens_" + str(i) + ".json", common)
            output = self.write("old_output_" + str(i) + ".json", dict(**common, raw_text=text, raw_token_ref=token))
            outputs.append(output)
            details.append(dict(uid=uid, sid=request["sid"], output_ref=output))
        self.old_completion = dict(status="PASS_ALL43_MATCHED_SUMMARY_GENERATIONS", model_role="INIT_TIME",
            optimizer_updates=0, old_TIME_unchanged=True, base_fingerprint=self.base,
            model_weights_ref=reference(weights), input_acceptance_ref=gate, outputs=outputs)
        self.old_qa = dict(status="PASS_ALL43_FIRST_INDEPENDENT_SUMMARY_TOKEN_GRAMMAR_NATIVE_QA",
            model_role="INIT_TIME", windows=43, sources=8, invalid_outputs=0, unique_ledger_equal=True,
            outputs=outputs, details=details,
            resource_ref=self.write("old_resource.json", dict(status="completed", exit_code=0)))
        self.bind_origin()

    def write(self, name, value):
        path = self.path / name
        path.write_text(json.dumps(value), encoding="utf-8")
        return reference(path)

    def bind_origin(self):
        completion_ref = self.write("old_completion.json", self.old_completion)
        self.old_qa["completion_ref"] = completion_ref
        self.manifest["reference_generation_origin"] = dict(completion_ref=completion_ref,
            first_output_qa_ref=self.write("old_qa.json", self.old_qa))

    def adopt(self):
        store = self.store_factory(self.manifest, "check")
        store.case = lambda uid: (_ for _ in ()).throw(AssertionError("Tensor loading is forbidden during adoption"))
        runtime = SimpleNamespace(tokenizer=Tokenizer(), eos=999, base_before=self.base)
        return adopt_reference(runtime, store, list(store.case_ids), self.manifest, self.directory,
            lambda *args: None, self.budget, summary_grammar6,
            summary_grammar6.ascii_token_candidates(runtime.tokenizer))

    def runtime_factory(self, *args, **kwargs):
        runtime = super().runtime_factory(*args, **kwargs)
        runtime.base_before = self.base
        fixture = self

        def train(pairs, get_input, cache, *, updates, grad_accum, lr, beta):
            assert runtime.state == "reference" and (updates, grad_accum, lr, beta) == (16, 2, 1e-5, .1)
            assert len(pairs) == 32 and len(cache["entries"]) == 48
            assert runtime.counts["generation_calls"] == 0
            fixture.trace.append(("train", tuple(pair["pair_id"] for pair in pairs)))
            for pair in pairs:
                get_input(pair["input_key"])
            runtime.teacher_scores(2 + 4 * len(pairs))
            runtime.counts.update(backward_calls=64, backwards_completed=64, optimizer_steps=16)
            runtime.state = "trained"
            return dict(synthetic_unit_test_only=True, completed_updates=16)

        runtime.train_pairs = train
        return runtime


class ReferenceAdoptionChecks(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix="aic_retained_reference_")
        self.addCleanup(self.temp.cleanup)
        self.fixture = OriginFixture(Path(self.temp.name))

    def test_complete_historical_empty_is_accepted_without_tensor_or_model_call(self):
        refs = self.fixture.adopt()
        self.assertEqual(len(refs), 43)
        for ref in refs:
            row = strict_load(ref["path"])
            self.assertTrue(row["legal_empty"])
            self.assertEqual(row["selected_ordinals"], [])
            self.assertTrue(row["adopted_historical_model_call"])
            self.assertEqual(row["new_model_calls"], 0)
            self.assertIn("historical_raw_token_ref", row)

    def test_wrong_base_identity_rejected(self):
        self.fixture.old_completion["base_fingerprint"] = dict(self.fixture.base, sha256="f" * 64)
        self.fixture.bind_origin()
        with self.assertRaisesRegex(ValueError, "base fingerprint differs"):
            self.fixture.adopt()

    def test_missing_output_is_failure_not_empty(self):
        Path(self.fixture.old_completion["outputs"][0]["path"]).unlink()
        with self.assertRaises(FileNotFoundError):
            self.fixture.adopt()
        self.assertFalse((self.fixture.directory / "reference_0000.json").exists())

    def test_wrong_qa_request_binding_rejected(self):
        self.fixture.old_qa["details"][0]["output_ref"] = self.fixture.old_completion["outputs"][1]
        self.fixture.bind_origin()
        with self.assertRaisesRegex(ValueError, "output/request/QA identity differs"):
            self.fixture.adopt()

    def test_real_manifest_without_origin_stops_before_model_load(self):
        del self.fixture.manifest["reference_generation_origin"]
        self.fixture.manifest["model_spec"].pop("synthetic_unit_test_only")
        with self.assertRaisesRegex(ValueError, "requires explicit historical reference"):
            self.fixture.invoke()
        self.assertEqual(self.fixture.trace, [])

    def test_pilot_adopts43_reference_and_makes_only43_new_policy_calls(self):
        completed = strict_load(self.fixture.invoke()["path"])
        self.assertEqual(completed["counts"]["generation_calls"], 43)
        self.assertEqual(completed["counts"]["sequence_score_calls"], 258)
        self.assertEqual(completed["counts"]["backwards_completed"], 64)
        self.assertEqual(completed["counts"]["optimizer_steps"], 16)
        self.assertEqual(completed["historical_reference_generations_adopted"], 43)
        self.assertEqual(completed["new_reference_generation_calls"], 0)
        self.assertEqual([row for row in self.fixture.trace if row[:2] == ("generate", "reference")], [])
        self.assertEqual(len([row for row in self.fixture.trace if row[:2] == ("generate", "policy")]), 43)


if __name__ == "__main__":
    unittest.main()
