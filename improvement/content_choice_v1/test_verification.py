"""Synthetic CPU identity, call-accounting and read-only DPO regressions.

Fixtures contain invented JSON/numeric receipts, not real model results. Actual
Torch reconstruction is separately mandatory in torch_checks (cannot be
satisfied by these tests). No Torch, tokenizer, media, model or GPU is used.
"""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest

from .contracts import (FROZEN_PIPELINE, admission_gate, claim, reference,
    save_new, strict_load, validate_config, HERE)
from .dpo_diagnostic import diagnose
from .verification import (frozen_receipt, collection_call_counts, check_call_counts,
                           original_request_core_equal)


class ContractTests(unittest.TestCase):
    def test_configuration_freezes_science_and_only_tightens_resources(self):
        original = strict_load(HERE / "config.example.json")
        validate_config(original)
        lower = dict(original, max_output_bytes=1, max_collect_train_seconds=1)
        validate_config(lower)
        for key, value in (("temperature", .81), ("samples", 3), ("ridge", .02),
                           ("official_training_or_pseudolabels", True), ("max_new_tokens", 511),
                           ("max_collect_train_seconds", 7201), ("automatic_production", True)):
            with self.subTest(key=key), self.assertRaises(ValueError):
                validate_config(dict(original, **{key: value}))
        with self.assertRaises(ValueError):
            validate_config(dict(original, latest_version=True))

    def test_claim_is_exclusive_and_cannot_enter_an_adopted_asset_tree(self):
        with tempfile.TemporaryDirectory() as name:
            root = Path(name)
            model = root / "model"; model.mkdir()
            historical = save_new(root / "historical.json", dict(status="FAILED_PRESERVED"))
            manifest = dict(workspace_root=name, model_spec=dict(model_dir=str(model)), historical=historical)
            config = dict(run_id="new_run", run_root=str(root / "new_run"))
            result = claim(config, manifest, "plan", dict(synthetic=True))
            before = (result / "claim.json").read_bytes()
            with self.assertRaises(FileExistsError):
                claim(config, manifest, "plan", dict(synthetic=True))
            self.assertEqual((result / "claim.json").read_bytes(), before)
            nested = root / "bad"; nested.mkdir()
            manifest["adopted"] = save_new(nested / "raw.json", dict(raw="original"))
            with self.assertRaises(ValueError):
                claim(dict(run_id="bad", run_root=str(nested)), manifest, "plan", {})
            self.assertEqual(strict_load(historical["path"])["status"], "FAILED_PRESERVED")

    def test_candidate_action_and_exact_evidence_all_bind_admission(self):
        with tempfile.TemporaryDirectory() as name:
            ref = save_new(Path(name) / "result.json", dict(value="synthetic"))
            expected = dict(review_ref=ref)
            good = dict(schema="AIC_CONTENT_CHOICE_ADMISSION_V1", candidate="critic", action="production",
                approved=True, reviewed_by="SYNTHETIC_TEST", reviewed_at="2026-10-19T00:00:00Z",
                review_notes="Synthetic interface test; no production authorization", **expected)
            admission_gate(good, "production", "critic", expected, name)
            for key, value in (("candidate", "contrast"), ("action", "package"), ("approved", False),
                               ("reviewed_by", " "), ("reviewed_at", "2026-10-19T00:00:00")):
                with self.subTest(key=key), self.assertRaises(ValueError):
                    admission_gate(dict(good, **{key: value}), "production", "critic", expected, name)
            (Path(name) / "result.json").write_text('{"value":"changed"}')
            with self.assertRaises(ValueError):
                admission_gate(good, "production", "critic", expected, name)

    def test_no_effect_allows_only_added_provenance_without_input_drift(self):
        original = dict(uid="w", sid="s", source_sha256="a" * 64,
            plan=dict(start="0", end="2"), text=dict(prompt="original"),
            input_signature=dict(input_ids="same", pixel_values_videos="same"), prefix_ref=dict(sha256="old"))
        adopted = dict(deepcopy(original), old_input_ref={"sha256": "origin"}, observation_policy="new")
        self.assertTrue(original_request_core_equal(adopted, original))
        for key in original:
            with self.subTest(key=key):
                bad = deepcopy(adopted); bad[key] = "changed"
                self.assertFalse(original_request_core_equal(bad, original))


class ReceiptTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        counts = dict(sequence_score_calls=4, sequence_scores_completed=4, generation_calls=2,
            generations_completed=2, top_level_forward_calls=10, backward_calls=0,
            backwards_completed=0, optimizer_steps=0, sample_generation_calls=2, samples_completed=2,
            feature_score_calls=4, feature_scores_completed=4)
        identity = dict(schema="AIC_CONTENT_CHOICE_RUNTIME_V1", active_weights="ORIGINAL_TIME_UNCHANGED",
            optimizer_updates=0, conservative_full_pipeline_parameters=FROZEN_PIPELINE,
            base_sha256="a" * 64, versions={"torch": "SYNTHETIC"})
        self.frozen = dict(schema="AIC_CONTENT_CHOICE_FROZEN_VERIFICATION_V1", counts=deepcopy(counts),
            runtime=deepcopy(identity), original_TIME_files_unchanged=True, changed_adapter_matrices=0,
            optimizer_steps=0, backward_calls=0, inventory=dict(conservative_full_pipeline=FROZEN_PIPELINE),
            base=dict(sha256="a" * 64))
        self.value = dict(runtime=identity, counts=counts,
            frozen_verification_ref=save_new(self.root / "frozen.json", self.frozen),
            event_journal_ref=save_new(self.root / "journal.json", {}),
            torch_checks_ref=save_new(self.root / "gate.json", {"status": "SYNTHETIC_REFERENCE_ONLY"}))

    def tearDown(self):
        self.temp.cleanup()

    def test_consistent_synthetic_receipt_is_read_but_does_not_claim_torch_gate(self):
        self.assertEqual(frozen_receipt(self.value, self.root), self.frozen)

    def test_runtime_versions_counts_or_parameter_bytes_cannot_drift(self):
        for change in ("runtime", "counts", "base", "frozen", "parameters"):
            with self.subTest(change=change):
                value = deepcopy(self.value); report = deepcopy(self.frozen)
                if change == "runtime":
                    value["runtime"]["versions"]["torch"] = "ANOTHER_ENVIRONMENT"
                elif change == "counts":
                    value["counts"]["generations_completed"] = 1
                elif change == "base":
                    report["base"]["sha256"] = "b" * 64
                elif change == "frozen":
                    report["changed_adapter_matrices"] = 1
                else:
                    report["inventory"]["conservative_full_pipeline"] += 131
                value["frozen_verification_ref"] = save_new(self.root / ("changed_" + change + ".json"), report)
                with self.assertRaises(ValueError):
                    frozen_receipt(value, self.root)

    def test_self_consistent_failed_counts_or_gradients_are_not_a_success(self):
        for key, number in (("optimizer_steps", 1), ("backward_calls", 1),
                            ("feature_scores_completed", 3), ("samples_completed", 1),
                            ("top_level_forward_calls", 5)):
            with self.subTest(key=key):
                value, report = deepcopy(self.value), deepcopy(self.frozen)
                value["counts"][key] = report["counts"][key] = number
                value["frozen_verification_ref"] = save_new(self.root / (key + ".json"), report)
                with self.assertRaises(ValueError):
                    frozen_receipt(value, self.root)


def synthetic_window(*, shifted=True, identical=False):
    real_signature = dict(input_ids="p", attention_mask="m", video_grid_thw="g", pixel_values_videos="v")
    shifted_signature = dict(real_signature, pixel_values_videos="v" if identical else "rotated")
    base = dict(logprob=-2.0, suffix_tokens=2, feature=[1.0] * 128, feature_position=3, actual_model_call=True)
    shifted_score = (dict(base, actual_model_call=False, identity_cache_alias=True) if identical else
                     dict(base, logprob=-3.0)) if shifted else None
    slots = []
    for slot, ids in enumerate(([1, 9], [1, 9], [1, 9], [2, 9])):
        slots.append(dict(slot=slot, ids=ids, real=deepcopy(base), permuted=deepcopy(shifted_score),
                          score_cache_first_slot=0 if slot < 3 else 3))
    return dict(slots=slots, counterfactual="ROTATION" if shifted else None,
        input_signature=real_signature, counterfactual_input_signature=shifted_signature if shifted else None,
        counterfactual_identical_input=identical)


class CallAccountingTests(unittest.TestCase):
    def test_exact_suffix_duplicates_save_calls_without_claiming_native_equal_is_enough(self):
        row = synthetic_window()
        self.assertEqual(collection_call_counts({"w": row}, adopted=True),
            dict(generation_calls=2, sample_generation_calls=2, sequence_score_calls=4))
        row["slots"][1]["ids"] = [7, 9]
        row["slots"][1]["score_cache_first_slot"] = 1
        self.assertEqual(collection_call_counts({"w": row}, adopted=False)["sequence_score_calls"], 6)

    def test_identical_real_counterfactual_is_an_explicit_zero_extra_forward_alias(self):
        row = synthetic_window(identical=True)
        self.assertEqual(collection_call_counts({"w": row}, adopted=True)["sequence_score_calls"], 2)
        row["slots"][0]["permuted"]["logprob"] = -99.0
        with self.assertRaises(ValueError):
            collection_call_counts({"w": row}, adopted=True)

    def test_missing_counterfactual_has_no_invented_score(self):
        row = synthetic_window(shifted=False)
        self.assertEqual(collection_call_counts({"w": row}, adopted=True)["sequence_score_calls"], 2)
        row["slots"][0]["permuted"] = row["slots"][0]["real"]
        with self.assertRaises(ValueError):
            collection_call_counts({"w": row}, adopted=True)

    def test_bad_cache_alias_or_incomplete_actual_calls_are_rejected(self):
        row = synthetic_window()
        row["slots"][1]["real"]["feature"][0] = 2
        with self.assertRaises(ValueError):
            collection_call_counts({"w": row}, adopted=True)
        with self.assertRaises(ValueError):
            check_call_counts(dict(generation_calls=1), dict(generation_calls=2))


class FrozenDpoDiagnosticTests(unittest.TestCase):
    def fixture(self, root, *, duplicate=False):
        pairs, before, after = [], [], []
        for i in range(16):
            pid, sid = f"p{i}", f"s{i // 2}"
            pairs.append(dict(pair_id=pid, source_id=sid, chosen_ids=[1, 2, 9], rejected_ids=[1, 3, 9]))
            before.append(dict(pair_id=pid, source_id=sid, chosen_logprob=-10., rejected_logprob=-11.))
            after.append(dict(pair_id=pid, source_id=sid, chosen_logprob=-11., rejected_logprob=-13.))
        if duplicate:
            before.append(deepcopy(before[0]))
        prepared = save_new(root / "prepared.json", dict(check_pairs=pairs))
        scores = save_new(root / "scores.json", dict(reference=before, policy=after))
        completed = save_new(root / "completed.json", dict(status="COMPLETE_PILOT_NOT_ADMITTED",
            counts=dict(sequence_scores_completed=258, backwards_completed=64, optimizer_steps=16, generations_completed=43),
            prepared_ref=prepared, heldout_pair_scores_ref=scores))
        reviewed = save_new(root / "review.json", dict(status="STOP_MECHANISM", pilot_completion_ref=completed,
            stop_reasons=["ORIGINAL_FROZEN_STOP_SYNTHETIC_FIXTURE"]))
        return completed["path"], reviewed["path"]

    def test_relative_improvement_and_both_absolute_probabilities_falling_coexist(self):
        with tempfile.TemporaryDirectory() as name:
            paths = self.fixture(Path(name))
            original = {p: Path(p).read_bytes() for p in paths}
            result = diagnose(*paths, name)
            self.assertEqual(result["both_absolute_logps_fell"], 16)
            self.assertTrue(result["original_stop_unchanged"])
            self.assertEqual(result["actual_new_qwen_calls"], 0)
            self.assertTrue(all(p["relative_margin_delta"] == 1 and p["shared_suffix_prefix_tokens"] == 1
                                for p in result["pairs"]))
            self.assertEqual({p: Path(p).read_bytes() for p in paths}, original)

    def test_extra_duplicate_evaluation_pair_cannot_be_silently_deduplicated(self):
        with tempfile.TemporaryDirectory() as name:
            with self.assertRaises(ValueError):
                diagnose(*self.fixture(Path(name), duplicate=True), name)


if __name__ == "__main__":
    unittest.main(verbosity=2)
