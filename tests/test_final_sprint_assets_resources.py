"""Synthetic binding/resource tests only; no426 media, GPU or quality claim."""
from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest.mock import patch

from improvement.final_sprint_v1 import assets, resources
from improvement.final_sprint_v1.contracts import ref, save_new, stable_key, strict_load
from improvement.final_sprint_v1.inventory import inventory_factory


class ResourceTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.assets = {"run_root": str(self.root / "run"),
            "deadline": (datetime.now(timezone.utc) + timedelta(hours=24)).isoformat(),
            "resources": {"scratch_dir": str(self.root), "planned_output_bytes": 100,
                "planned_scratch_bytes": 200, "disk_reserve_bytes": 50, "planned_ram_bytes": 100,
                "ram_reserve_bytes": 50, "required_gpu_memory_bytes": 100,
                "cpu_threads": 2, "gpu_index": 0, "finalization_reserve_seconds": 600,
                "total_execution_seconds": 60}}

    def tearDown(self):
        self.temporary.cleanup()

    def test_same_filesystem_output_scratch_peak_must_be_combined(self):
        with patch.object(resources.shutil, "disk_usage", return_value=SimpleNamespace(free=250)):
            with self.assertRaisesRegex(ValueError, "combined output/scratch"):
                resources.snapshot(self.assets)

    def test_tmpfs_free_is_not_physical_memory(self):
        with patch.object(resources.shutil, "disk_usage", return_value=SimpleNamespace(free=1000)), \
             patch.object(resources, "_memory_available", return_value=149):
            with self.assertRaisesRegex(ValueError, "MemAvailable"):
                resources.snapshot(self.assets)

    def test_negative_reserves_and_bool_threads_cannot_bypass_gate(self):
        for name, value in (("planned_scratch_bytes", -1), ("disk_reserve_bytes", -1),
                            ("required_gpu_memory_bytes", -1), ("finalization_reserve_seconds", -1),
                            ("cpu_threads", True)):
            old = self.assets["resources"][name]
            self.assets["resources"][name] = value
            with self.assertRaisesRegex(ValueError, "resource limit"):
                resources.snapshot(self.assets)
            self.assets["resources"][name] = old

    def test_gpu_absence_is_not_production_success(self):
        with patch.object(resources.shutil, "disk_usage", return_value=SimpleNamespace(free=1000)), \
             patch.object(resources, "_memory_available", return_value=1000), \
             patch.object(resources, "_run", side_effect=FileNotFoundError("no GPU here")):
            self.assertEqual(resources.snapshot(self.assets)["gpus"], "UNAVAILABLE")
            with self.assertRaisesRegex(ValueError, "Real Linux NVIDIA"):
                resources.snapshot(self.assets, require_gpu=True)

    def test_foreign_gpu_requires_fresh_real_grant(self):
        now = datetime.now(timezone.utc)
        grant = {"status": "GRANTED", "gpu_uuid": "GPU-test", "run_root": self.assets["run_root"],
            "reservation_id": "owned-registered-task", "issued_at": (now - timedelta(hours=2)).isoformat(),
            "expires_at": (now - timedelta(hours=1)).isoformat()}
        self.assets["resources"]["shared_gpu_grant"] = save_new(self.root / "expired.json", grant)
        with patch.object(resources.shutil, "disk_usage", return_value=SimpleNamespace(free=1000)), \
             patch.object(resources, "_memory_available", return_value=1000), \
             patch.object(resources, "_run", side_effect=["0, GPU-test, 48000, 40000, 10", "GPU-test, 98765, 100"]):
            with self.assertRaisesRegex(ValueError, "not currently valid"):
                resources.snapshot(self.assets, require_gpu=True)

    def test_command_wall_accounting_deduplicates_finish_and_failure(self):
        with patch.object(resources.time, "monotonic", side_effect=[100, 105]):
            budget = resources.Budget(self.assets, "smoke", 20)
            first = budget.finish("FAILED", error=RuntimeError("smoke failed"))
        self.assertEqual(first["wall_seconds_including_load_decode_failures"], 5)
        self.assertEqual(budget.finish("FAILED"), first)
        summary = resources.cumulative_execution(self.assets)
        self.assertEqual(summary["confirmed_command_wall_seconds"], 5)
        self.assertEqual(summary["unresolved_reserved_seconds"], 0)

    def test_unresolved_command_reserves_cap_until_exact_terminal(self):
        budget = resources.Budget(self.assets, "production", 20)
        before = resources.cumulative_execution(self.assets)
        self.assertEqual(before["unresolved_reserved_seconds"], 20)
        proof = save_new(self.root / "terminal.json", {"command_id": budget.command_id,
            "work_terminated": True, "termination_basis": "owned_wrapper_terminal",
            "no_external_task_signaled": True, "claim_sha256": ref(budget.folder / "claim.json")["sha256"],
            "wall_seconds_including_load_decode_failures": 7.5})
        resources.resolve_command_budget(self.assets, budget.command_id, proof)
        after = resources.cumulative_execution(self.assets)
        self.assertEqual(after["confirmed_command_wall_seconds"], 7.5)
        self.assertEqual(after["unresolved_reserved_seconds"], 0)

    def test_claim_before_index_crash_still_reserves_and_reconciles_exact_cost(self):
        budget = resources.Budget(self.assets, "production", 20)
        (budget.directory / "index.json").unlink()  # Durable claim preceded index publication.
        before = resources.cumulative_execution(self.assets)
        self.assertEqual(before["unresolved_reserved_seconds"], 20)
        proof = save_new(self.root / "orphan_command_terminal.json", {"command_id": budget.command_id,
            "work_terminated": True, "termination_basis": "owned_wrapper_terminal",
            "no_external_task_signaled": True, "claim_sha256": ref(budget.folder / "claim.json")["sha256"],
            "wall_seconds_including_load_decode_failures": 4.5})
        resources.resolve_command_budget(self.assets, budget.command_id, proof)
        after = resources.cumulative_execution(self.assets)
        self.assertEqual(after["confirmed_command_wall_seconds"], 4.5)
        self.assertEqual(after["unresolved_reserved_seconds"], 0)
        another = resources.Budget(self.assets, "next", 5)
        self.assertEqual(set(strict_load(another.directory / "index.json")["command_ids"]),
                         {budget.command_id, another.command_id})
        another.finish()

    def test_cumulative_cap_and_negative_next_estimate(self):
        self.assets["resources"]["total_execution_seconds"] = 2
        budget = resources.Budget(self.assets, "source", 5)
        self.assertEqual(budget.cap, 2)
        with self.assertRaisesRegex(ValueError, "nonnegative"):
            budget.check(-1)
        with self.assertRaisesRegex(ValueError, "exhausted or reserved"):
            resources.Budget(self.assets, "another", 1)
        budget.finish("STOPPED")

    def test_context_entry_failure_records_zero_work_failure_terminal(self):
        self.assets["deadline"] = (datetime.now(timezone.utc) + timedelta(seconds=30)).isoformat()
        budget = resources.Budget(self.assets, "smoke", 5)
        with self.assertRaisesRegex(ValueError, "reserve"):
            with budget:
                self.fail("Deadline failure must happen before this body")
        self.assertEqual(budget.terminal["status"], "FAILED")


class AssetHelperTests(unittest.TestCase):
    def test_legacy_path_sha_measures_size_without_replacing_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "original.json"
            path.write_text('{"original":true}')
            complete = ref(path)
            legacy = {key: complete[key] for key in ("path", "sha256")}
            self.assertEqual(assets._identity(legacy), complete)
            self.assertNotIn("bytes", legacy)
            wrong = dict(legacy, sha256="0" * 64)
            with self.assertRaisesRegex(ValueError, "SHA256"):
                assets._identity(wrong)

    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_existing_full_color_config_is_bound_and_normalized(self):
        sha = "a" * 64
        source = {"format": "yuv420p", "width": 100, "height": 80, "color_trc": 18,
                  "colorspace": 1, "color_primaries": 9, "color_range": 1}
        config = {"source_color_repair": {"sources": {sha: source},
                                         "matrix": "bt709", "transfer_tag_for_conversion": 1}}
        identity = save_new(self.root / "baseline_config.json", config)
        normalized, bound = assets.normalize_color_policy(identity)
        self.assertEqual(bound, identity)
        self.assertEqual(normalized[sha]["source_sha256"], sha)
        self.assertEqual(normalized[sha]["matrix"], "bt709")
        self.assertEqual(normalized[sha]["color_trc"], 18)

    def test_incomplete_color_policy_does_not_silently_disable_repair(self):
        with self.assertRaisesRegex(ValueError, "Incomplete original"):
            assets.normalize_color_policy({"sources": {"a" * 64: {}}})

    def test_model_loader_visible_symlink_retarget_is_detected(self):
        model = self.root / "model"
        model.mkdir()
        first = self.root / "first.json"
        second = self.root / "second.json"
        first.write_text('{"processor":"original"}')
        second.write_text('{"processor":"changed"}')
        link = model / "tokenizer_config.json"
        link.symlink_to(first)
        tree = assets._tree(model)
        assets._validate_tree(tree)
        link.unlink()
        link.symlink_to(second)
        with self.assertRaisesRegex(ValueError, "symlink target changed"):
            assets._validate_tree(tree)

    def test_new_preferred_weight_file_cannot_bypass_bound_shards(self):
        model = self.root / "model"
        model.mkdir()
        (model / "model-00001.safetensors").write_bytes(b"bound shard")
        tree = assets._tree(model)
        (model / "model.safetensors").write_bytes(b"new preferred unbound model")
        with self.assertRaisesRegex(ValueError, "members changed"):
            assets._validate_tree(tree)

    def test_inventory_success_reused_without_torch_or_factory_reload(self):
        weights = self.root / "tiny.weights"
        weights.write_bytes(b"synthetic-only")
        weight_ref = ref(weights)
        spec = {"schema": "AIC_FINAL_INVENTORY_FACTORY_V1", "component_id": "tiny",
                "factory": {"this_must_not_load": True}}
        receipt = {"schema": "AIC_FINAL_PARAMETERS_V1", "origin": "actual_loaded", "component_id": "tiny",
            "weight_files": [weight_ref], "total_elements": 2, "quantization_does_not_reduce_parameters": True,
            "tensors": [{"shape": [2], "elements": 2, "name": "weight", "aliases": ["weight"],
                "source": {"weight_sha256": weight_ref["sha256"], "tensor_name": "weight"}}],
            "loading_proof": {"factory_spec_sha256": stable_key(spec), "code_refs": []}}
        output = self.root / "inventory.json"
        save_new(output, receipt)
        result = inventory_factory(spec, output_path=output)
        self.assertTrue(result["adopted_existing_success_no_model_reload"])
        self.assertEqual(result["total_elements"], 2)


if __name__ == "__main__":
    unittest.main()
