"""Public synthetic plumbing tests, not actual model/media/quality validation."""
import copy
from datetime import datetime, timedelta, timezone
import os
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from improvement.final_sprint_v1 import bootstrap as b
from improvement.final_sprint_v1.contracts import atomic_new, ref, stable_key, strict_load


class BootstrapTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, relative, value):
        path = self.root / relative
        path.parent.mkdir(parents=True, exist_ok=True)
        if isinstance(value, bytes):
            path.write_bytes(value)
        else:
            atomic_new(path, value)
        return ref(path)

    def test_original_sha_is_verified_and_never_replaced(self):
        identity = self.write("head.pt", b"synthetic checkpoint")
        legacy = {"path": identity["path"], "sha256": identity["sha256"]}
        self.assertEqual(b.registered_ref(legacy, "head"), identity)
        bad = dict(legacy, sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "SHA256 changed"):
            b.registered_ref(bad, "head")

    def test_exact_original_runtime_comes_from_original_lock(self):
        runtime = self.write("engineering/runtime.py", b"def make_models(root): pass\n")
        registration = self.write("routing/registration.json", {"synthetic": True})
        self.write("routing/source_input_lock.json", {
            "registration": registration, "dependencies": {runtime["path"]: runtime}})
        actual, lock = b._original_runtime(self.root / "engineering", registration)
        self.assertEqual(actual, runtime)
        self.assertEqual(Path(lock["path"]).name, "source_input_lock.json")
        wrong = dict(registration, sha256="0" * 64)
        with self.assertRaisesRegex(ValueError, "another registration"):
            b._original_runtime(self.root / "engineering", wrong)

    def test_missing_runtime_lock_never_searches_other_vn(self):
        runtime = self.write("engineering/runtime.py", b"def make_models(root): pass\n")
        another = self.write("engineering/crossdata12/code/runtime.py", b"def make_models(root): pass\n")
        registration = self.write("routing/registration.json", {"synthetic": True})
        self.write("routing/source_input_lock.json", {
            "registration": registration, "dependencies": {another["path"]: another}})
        with self.assertRaisesRegex(ValueError, "exactly ENGINEERING/runtime.py"):
            b._original_runtime(Path(runtime["path"]).parent, registration)

    def test_factory_specs_select_real_registered_state_containers(self):
        module = self.write("runtime.py", b"def make_models(root): pass\n")
        checkpoint = self.write("I3D.pyth", b"synthetic")
        provenance = {"registration_refs": {"config": self.write("config.json", {})}}
        spec = b._factory_spec("i3d", module, [], checkpoint, ["model_state"],
                               [str(self.root)], [0], provenance)
        self.assertEqual(spec["factory"]["callable"], "make_models")
        self.assertEqual(spec["factory"]["output_selector"], [0])
        self.assertEqual(spec["checkpoint"]["state_path"], ["model_state"])
        self.assertEqual(spec["checkpoint"]["ref"], checkpoint)
        self.assertEqual(spec["baseline_provenance"], provenance)
        self.assertNotIn("expected_parameters", spec)

    def adopted(self):
        asset = self.write("old/asset.json", {"synthetic": True})
        model = self.root / "old/model"
        model.mkdir()
        provenance = {"registration_refs": {"config": asset}, "checkpoint_refs": {},
                      "synthetic_test_only": True}
        specs = {}
        for component in b.COMPONENTS:
            weight = self.write("old/" + component + ".pt", component.encode())
            provenance["checkpoint_refs"][component] = weight
        for component in b.COMPONENTS:
            specs[component] = {"schema": "AIC_FINAL_LORA_INVENTORY_V1" if component == "original_time"
                              else "AIC_FINAL_INVENTORY_FACTORY_V1", "component_id": component,
                              "baseline_provenance": provenance}
        return {"registrations": {"config": asset, "package_inputs": asset}, "provenance": provenance,
                "specs": specs, "baselines": {"40.48": asset, "40.47": asset},
                "qwen": {"model_dir": str(model), "revision": "synthetic_test"},
                "protected_directories": [str(self.root / "old")], "inferred_workspace": str(self.root)}

    def prepare(self, adopted):
        kwargs = {key: "unused-synthetic-path" for key in ("config", "package_inputs", "semantic_registration",
                   "i3d_acceptance", "umt_registration", "baseline_40_48", "baseline_40_47")}
        kwargs.update(run_root=self.root / "new_run", scratch_dir=self.root,
                      deadline=(datetime.now(timezone.utc) + timedelta(hours=23)).isoformat())
        with patch.object(b, "_registered_assets", return_value=adopted):
            result = b.prepare(**kwargs)
            repeated = b.prepare(**kwargs)
        self.assertEqual(result, repeated)
        self.assertFalse((self.root / "new_run").exists())
        self.assertFalse((self.root / "new_run_binding/mapping.json").exists())
        return result, kwargs

    def test_prepare_is_idempotent_and_does_not_publish_unmeasured_mapping(self):
        result, kwargs = self.prepare(self.adopted())
        preparation = strict_load(result["preparation"]["path"])
        self.assertEqual(set(preparation["specs"]), set(b.COMPONENTS))
        resources = preparation["mapping_without_parameter_receipts"]["resources"]
        self.assertEqual(resources["planned_output_bytes"], 1 << 30)
        self.assertEqual(resources["ram_reserve_bytes"], 4 << 30)
        self.assertTrue(preparation["actual_inventory_required_before_mapping_publication"])
        self.assertEqual(preparation["media_decodes"], 0)

    def test_output_isolation_and_owner_drift_fail_before_overwriting(self):
        adopted = self.adopted()
        result, kwargs = self.prepare(adopted)
        before = Path(result["preparation"]["path"]).read_bytes()
        with patch.object(b, "_registered_assets", return_value=adopted):
            with self.assertRaisesRegex(ValueError, "another exact registration"):
                b.prepare(**dict(kwargs, gpu_index=1))
            with self.assertRaisesRegex(ValueError, "disjoint"):
                b.prepare(**dict(kwargs, output_dir=self.root / "new_run/inputs"))
            with self.assertRaisesRegex(ValueError, "protected dependency"):
                b.prepare(**dict(kwargs, run_root=self.root / "old/new_run"))
        self.assertEqual(Path(result["preparation"]["path"]).read_bytes(), before)

    def test_existing_inventory_success_is_adopted_without_reloading(self):
        adopted = self.adopted()
        result, _ = self.prepare(adopted)
        prepared_ref = result["preparation"]
        folder = self.root / "new_run_binding/inventories"
        folder.mkdir()
        expected_counts = {"original_time": b.TIME_PARAMETERS, "semantic_residual": b.SEMANTIC_PARAMETERS,
                           "i3d": b.AUX_PARAMETERS - 1, "sport_umt": 1}
        for component in b.COMPONENTS:
            spec = adopted["specs"][component]
            proof_key = "spec_sha256" if component == "original_time" else "factory_spec_sha256"
            # Deliberate small synthetic protocol double, never a production model inventory.
            value = {"schema": "SYNTHETIC_PROTOCOL_DOUBLE", "component_id": component,
                     "baseline_provenance": adopted["provenance"], "total_elements": expected_counts[component],
                     "bootstrap_preparation_ref": prepared_ref, "loading_proof": {proof_key: stable_key(spec)}}
            atomic_new(folder / (component + ".json"), value)
        with patch.object(b, "_validate_receipt") as verify, \
                patch.object(b, "total_parameters", return_value={"total_elements": sum(expected_counts.values())}), \
                patch("improvement.final_sprint_v1.inventory.inventory_factory") as factory, \
                patch("improvement.final_sprint_v1.inventory.inventory_lora_adapter") as lora:
            first = b.inventory(prepared_ref["path"])
            again = b.inventory(prepared_ref["path"])
        self.assertEqual(first, again)
        self.assertEqual(verify.call_count, 8)
        factory.assert_not_called()
        lora.assert_not_called()
        self.assertTrue(first["raw_BASE_inventory_and_real_smoke_pending"])

    def test_receipt_without_original_registration_binding_is_rejected(self):
        spec = {"component_id": "original_time", "baseline_provenance": {"expected": "original"}}
        value = {"schema": "AIC_FINAL_PARAMETERS_V1", "origin": "actual_loaded", "component_id": "original_time",
                 "loading_proof": {"spec_sha256": stable_key(spec)}}
        with self.assertRaisesRegex(ValueError, "original baseline registrations"):
            b._validate_receipt(value, spec, self.root / "unused")


if __name__ == "__main__":
    unittest.main()
