"""Synthetic CPU checks for stage/configuration/admission contracts only.

These checks neither import runtime/model code nor repeat pipeline evaluation.
Temporary JSON files are synthetic; no Linux asset or private reference is read.
"""

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from improvement.native_preference_v1 import contracts


def example_config():
    return contracts.strict_load(Path(__file__).with_name("config.example.json"))


class FrozenConfigurationTests(unittest.TestCase):
    def test_checked_in_recipe_is_valid_and_budget_can_only_tighten(self):
        config = example_config()
        self.assertIs(contracts.validate_config(config), config)
        self.assertEqual(config["updates"] * config["grad_accum"],
                         config["train_source_count"] * config["train_pairs_per_source"])
        reduced = copy.deepcopy(config)
        reduced["max_pilot_seconds"] //= 2
        reduced["max_production_top_level_forwards"] //= 2
        self.assertIs(contracts.validate_config(reduced), reduced)

    def test_cannot_silently_change_method_control_or_training_pass(self):
        changes = {
            "updates": 17,
            "train_source_count": 9,
            "seed": 20261020,
            "beta": 0.2,
            "learning_rate": 2e-5,
            "counterfactual": "MULTIPLE_SHIFT_SEARCH",
            "checkpoint": "BEST_CHECK_SCORE",
            "generation": "FORCE_NONEMPTY",
            "automatic_production": True,
            "automatic_submission": True,
            "historical_exposure": False,
        }
        for name, value in changes.items():
            config = example_config()
            config[name] = value
            with self.subTest(name=name), self.assertRaises(ValueError):
                contracts.validate_config(config)

    def test_exact_types_prevent_boolean_or_float_config_substitution(self):
        for name, value in (("updates", True), ("updates", 16.0),
                            ("automatic_production", 0),
                            ("max_pilot_seconds", 1.0), ("max_pilot_seconds", True)):
            config = example_config()
            config[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                contracts.validate_config(config)

    def test_expanded_nonpositive_or_nonfinite_budget_fails(self):
        for name, value in (("max_pilot_seconds", 3601), ("max_production_sources", 427),
                            ("max_top_level_forwards", 66001), ("max_output_bytes", 0),
                            ("max_production_top_level_forwards", 307201),
                            ("max_prepare_seconds", -1), ("learning_rate", float("inf")),
                            ("beta", float("nan"))):
            config = example_config()
            config[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                contracts.validate_config(config)

    def test_run_identity_and_required_configuration(self):
        for name, value in (("run_id", "../old_run"), ("run_id", "with spaces"),
                            ("run_id", ""), ("run_root", "relative/run")):
            config = example_config()
            config[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                contracts.validate_config(config)
        config = example_config()
        del config["generation"]
        with self.assertRaises(ValueError):
            contracts.validate_config(config)


class JsonAndAssetBindingTests(unittest.TestCase):
    def test_strict_json_rejects_duplicates_and_all_nonfinite_encodings(self):
        invalid = ['{"approved":false,"approved":true}', '{"x":NaN}',
                   '{"x":Infinity}', '{"x":-Infinity}', '{"x":1e309}', '{"x":-1e309}']
        with tempfile.TemporaryDirectory() as temporary:
            path = Path(temporary) / "synthetic.json"
            for text in invalid:
                path.write_text(text, encoding="utf-8")
                with self.subTest(text=text), self.assertRaises(ValueError):
                    contracts.strict_load(path)

    def test_bound_reference_rejects_changed_bytes_and_wrong_length(self):
        with tempfile.TemporaryDirectory() as temporary:
            root = Path(temporary)
            path = root / "asset.txt"
            path.write_text("original", encoding="utf-8")
            bound = contracts.reference(path)
            self.assertEqual(contracts.checked(bound, root), path)
            wrong_size = dict(bound, bytes=bound["bytes"] + 1)
            with self.assertRaises(ValueError):
                contracts.checked(wrong_size, root)
            path.write_text("modified", encoding="utf-8")
            with self.assertRaises(ValueError):
                contracts.checked(bound, root)

    def test_bound_reference_rejects_a_symlink_outside_its_root(self):
        with tempfile.TemporaryDirectory() as temporary:
            top = Path(temporary)
            root = top / "run"
            root.mkdir()
            outside = top / "unrelated.txt"
            outside.write_text("unrelated", encoding="utf-8")
            link = root / "looks_local.txt"
            link.symlink_to(outside)
            bound = contracts.reference(outside)
            bound["path"] = str(link)
            with self.assertRaises(ValueError):
                contracts.checked(bound, root)


class AdmissionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.expected = {}
        for kind in ("config_ref", "assets_ref", "review_ref", "adapter_ref"):
            path = self.root / (kind + ".txt")
            path.write_text("synthetic " + kind, encoding="utf-8")
            self.expected[kind] = contracts.reference(path)
        self.admission = dict(schema=contracts.ADMISSION_SCHEMA, action="production",
                              approved=True, reviewed_by="execution-agent",
                              review_notes="Reviewed this synthetic candidate and its bound assets.",
                              reviewed_at="2026-10-19T12:00:00Z", **copy.deepcopy(self.expected))

    def tearDown(self):
        self.temporary.cleanup()

    def test_exact_reviewed_assets_pass(self):
        self.assertIs(contracts.validate_admission(self.admission, "production", self.expected,
                                                  root=self.root), self.admission)

    def test_unapproved_wrong_action_or_missing_review_fails(self):
        for name, value in (("approved", False), ("approved", 1), ("action", "pilot"),
                            ("reviewed_by", " "), ("review_notes", ""),
                            ("reviewed_at", "2026-10-19T12:00:00")):
            admission = copy.deepcopy(self.admission)
            admission[name] = value
            with self.subTest(name=name, value=value), self.assertRaises(ValueError):
                contracts.validate_admission(admission, "production", self.expected, root=self.root)

    def test_no_asset_bindings_cannot_count_as_admission(self):
        with self.assertRaises(ValueError):
            contracts.validate_admission(self.admission, "production", {}, root=self.root)

    def test_missing_or_changed_asset_cannot_reuse_previous_admission(self):
        admission = copy.deepcopy(self.admission)
        del admission["assets_ref"]
        with self.assertRaises(ValueError):
            contracts.validate_admission(admission, "production", self.expected, root=self.root)
        path = self.root / "new_assets.txt"
        path.write_text("different actual assets", encoding="utf-8")
        expected = copy.deepcopy(self.expected)
        expected["assets_ref"] = contracts.reference(path)
        with self.assertRaises(ValueError):
            contracts.validate_admission(self.admission, "production", expected, root=self.root)

    def test_same_bytes_under_a_different_path_are_not_the_reviewed_asset(self):
        path = self.root / "copied_adapter.txt"
        original = Path(self.expected["adapter_ref"]["path"])
        path.write_bytes(original.read_bytes())
        self.assertEqual(contracts.reference(path)["sha256"], self.expected["adapter_ref"]["sha256"])
        admission = copy.deepcopy(self.admission)
        admission["adapter_ref"] = contracts.reference(path)
        with self.assertRaises(ValueError):
            contracts.validate_admission(admission, "production", self.expected, root=self.root)

    def test_file_modified_after_review_is_rejected_even_if_refs_still_agree(self):
        Path(self.expected["adapter_ref"]["path"]).write_text("changed after review", encoding="utf-8")
        with self.assertRaises(ValueError):
            contracts.validate_admission(self.admission, "production", self.expected, root=self.root)


class StageAndOutputTests(unittest.TestCase):
    def test_legal_empty_is_accepted_but_failed_or_missing_source_is_not(self):
        legal = {"source_a": dict(status="ACCEPTED", selected_ordinals=[])}
        self.assertIs(contracts.successful_source_selections(legal, ["source_a"]), legal)
        for records in ({}, {"source_a": dict(status="FAILED", selected_ordinals=[])},
                        {"source_a": dict(selected_ordinals=[])},
                        {**legal, "extra_source": dict(status="ACCEPTED", selected_ordinals=[])}):
            with self.subTest(records=records), self.assertRaises(ValueError):
                contracts.successful_source_selections(records, ["source_a"])

    def test_selected_ordinals_must_be_native_unique_sorted_integers(self):
        for selected in ([2, 1], [1, 1], [-1], [True], [1.0], None):
            with self.subTest(selected=selected), self.assertRaises(ValueError):
                contracts.successful_source_selections(
                    {"s": dict(status="ACCEPTED", selected_ordinals=selected)}, ["s"])

    def test_stage_cannot_be_reclaimed_or_overwrite_old_claim(self):
        with tempfile.TemporaryDirectory() as temporary:
            stage = contracts.claim_stage(temporary, "pilot", {"run_identity": "synthetic"})
            original = (stage / "claim.json").read_bytes()
            claim = json.loads(original)
            self.assertFalse(claim["automatic_retry"])
            self.assertFalse(claim["failed_output_to_empty"])
            with self.assertRaises(FileExistsError):
                contracts.claim_stage(temporary, "pilot", {"run_identity": "replacement"})
            self.assertEqual((stage / "claim.json").read_bytes(), original)
            with self.assertRaises(ValueError):
                contracts.claim_stage(temporary, "autofallback", {})

    def test_finite_stage_forward_wall_and_output_limits_without_sleep(self):
        with tempfile.TemporaryDirectory() as temporary:
            with patch.object(contracts.time, "monotonic", return_value=100.0) as clock:
                budget = contracts.StageBudget(temporary, seconds=1, output_bytes=5, forward_limit=2)
                budget.check(forward=True)
                budget.check(forward=True)
                with self.assertRaises(ValueError):
                    budget.check(forward=True)
                clock.return_value = 102.0
                with self.assertRaises(ValueError):
                    budget.check()
            path = Path(temporary) / "synthetic_output.bin"
            path.write_bytes(b"123456")
            budget = contracts.StageBudget(temporary, seconds=10, output_bytes=5, forward_limit=2)
            with self.assertRaises(ValueError):
                budget.check(force_disk=True)


if __name__ == "__main__":
    unittest.main()
