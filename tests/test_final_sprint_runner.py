"""Integration contracts with synthetic CPU objects, never quality evidence."""
from fractions import Fraction
import json
from pathlib import Path
import socket
import tempfile
import unittest
from unittest.mock import Mock, patch

from improvement.final_sprint_v1 import runner
from improvement.final_sprint_v1.contracts import ref, stable_key
from improvement.final_sprint_v1.supervise import terminal_claims


class RunnerContracts(unittest.TestCase):
    def test_first_write_creates_parent_and_exact_adoption_rejects_change(self):
        with tempfile.TemporaryDirectory() as directory:
            path = Path(directory) / "nested" / "new" / "receipt.json"
            first = runner.write_adopt(path, {"actual": 1})
            self.assertEqual(first, runner.write_adopt(path, {"actual": 1}))
            with self.assertRaisesRegex(ValueError, "differs"):
                runner.write_adopt(path, {"actual": 2})

    def test_cpu_only_apex_cannot_start_missing_phase_inference(self):
        engine = runner.Engine.__new__(runner.Engine)
        engine.assets = {"qwen": {"asset_tree": {"bound": True}}}
        engine.candidate = runner.asset_api.candidate_registry()["candidates"]["r_phase_apex"]
        engine.journal = Mock()
        engine.journal.get.return_value = None
        item = {"video_id": "s", "media": {"sha256": "a" * 64}, "clock": {"bound": True},
                "normalized_exact_pts": [str(Fraction(i, 4)) for i in range(16)],
                "physical_end_exact": "4", "n_frames": 16}
        with patch.object(runner, "iter_decoded_clips") as decoding:
            with self.assertRaisesRegex(ValueError, "CPU-only"):
                engine.phases(item, cached_only=True)
            decoding.assert_not_called()

    def test_parent_file_tamper_cannot_be_rebound_as_new_evidence(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = runner.Engine.__new__(runner.Engine)
            engine.root, engine.assets, engine.assets_path = Path(directory), {}, "unused"
            engine.journal = Mock()
            engine.journal.get.return_value = {"prediction": "original"}
            path = engine.root / "candidates" / "g_subject" / "sources" / "0" / "result.json"
            runner.write_adopt(path, {"prediction": "modified"})
            with patch.object(runner.asset_api, "binding", return_value={"exact": 1}):
                with self.assertRaisesRegex(ValueError, "durable successful"):
                    engine.parent_source("g_subject", {"video_id": "0", "media": {}, "clock": {}})

    def test_g_smoke_requires_all_auxiliary_models_before_any_gpu_call(self):
        with patch.object(runner, "gpu_lease") as gpu:
            with self.assertRaisesRegex(ValueError, "inventories before"):
                runner.smoke({"baseline_parameter_receipts": []}, "unused", "g_subject")
            gpu.assert_not_called()

    def test_wrapper_proves_only_exact_owned_claims(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            own = root / "journal" / "tasks" / "one" / "attempts" / "1" / "claim.json"
            other = root / "journal" / "tasks" / "two" / "attempts" / "1" / "claim.json"
            payload = {"owned_wrapper_id": "exact", "pid": 777, "host": socket.gethostname(),
                       "task_id": "one", "attempt": 1}
            runner.write_adopt(own, payload)
            runner.write_adopt(other, dict(payload, owned_wrapper_id="foreign", task_id="two"))
            destination = root / "terminal"
            destination.mkdir()
            tasks, commands = terminal_claims(root, "exact", 777, 3.25, destination)
            self.assertEqual([row["task_id"] for row in tasks], ["one"])
            self.assertEqual(commands, [])
            proof = json.loads(Path(tasks[0]["terminal_ref"]["path"]).read_text())
            self.assertEqual(proof["claim_sha256"], ref(own)["sha256"])
            self.assertTrue(proof["work_terminated"])

    def test_delivery_contains_only_small_public_transfer_identity(self):
        with tempfile.TemporaryDirectory() as directory:
            receipt = {"candidate_id": "example", "status": "ENGINEERING_ACCEPTED_QUALITY_UNVALIDATED",
                "zip_ref": {"path": "/linux/private/package.zip", "bytes": 5, "sha256": "a" * 64},
                "member_sha256": "b" * 64, "prediction_sha256": "c" * 64,
                "parameter_budget": {"total_elements": 8767123696}, "changes_from_baselines": {},
                "output_dir": directory}
            result = runner.delivery_manifest(receipt, {"source_commit": {"commit": "d" * 40}})
            value = Path(result["path"]).read_text()
            self.assertNotIn("/linux/private", value)
            self.assertNotIn("asset_lock", value)
            self.assertEqual(json.loads(value)["zip_filename"], "package.zip")

    def test_phase_runtime_uses_all_registered_algorithm_options(self):
        registered = runner.asset_api.candidate_registry()["candidates"]["r_phase_event"]
        changed = dict(registered, configuration=dict(registered["configuration"],
            clip_seconds=4, samples_per_clip=16, duration_fraction="1/5",
            event_start_penalty=.25, cost_resolution_ms=2))
        options = runner.phase_options(changed)
        self.assertEqual(options, {"clip_seconds": 4, "samples_per_clip": 16,
            "fraction": Fraction(1, 5), "segment_penalty": .25,
            "cost_resolution_ms": 2, "event_utility": "duration_integral"})

    def test_registered_specialist_recipe_reaches_runtime_and_rejects_drift(self):
        registered = runner.asset_api.candidate_registry()["candidates"]["m_specialist"]
        options = runner.specialist_options(registered)
        self.assertEqual(options.maximum_window_cells, 75)
        self.assertEqual(options.cell_seconds, "2")
        changed = dict(registered, configuration=dict(registered["configuration"], cell_seconds=3))
        with self.assertRaisesRegex(ValueError, "two-second"):
            runner.specialist_options(changed)

    def test_grounding_plan_counts_native_time_threshold_and_selection_gap(self):
        sources = [
            {"video_id": "gap", "normalized_exact_pts": ["0", "1/4", "19/10", "2", "41/20", "21/10", "11/5"]},
            {"video_id": "empty", "normalized_exact_pts": ["0", "1/30"]},
        ]
        baseline = {"gap": {index: [0, 0, 8] for index in (0, 1, 2, 3, 5, 6)}, "empty": {}}
        # Anchors are0(initial),3(exactly2s),5(an ordinal gap despite only0.1s
        # since the prior anchor). Ordinary adjacent frames add no model call.
        result = runner.grounding_plan(sources, baseline,
            {"ground_interval_seconds": 2, "max_ground_calls": 2})
        self.assertEqual(result["minimum_ground_calls"], 3)
        self.assertEqual(result["maximum_source_minimum_calls"], 3)
        self.assertEqual(result["sources_impossible_under_fixed_cap"],
                         [{"video_id": "gap", "mandatory_calls": 3}])
        admitted = runner.grounding_plan(sources, baseline,
            {"ground_interval_seconds": 2, "max_ground_calls": 3})
        self.assertEqual(admitted["sources_impossible_under_fixed_cap"], [])
        self.assertTrue(admitted["not_an_upper_bound_or_completion_guarantee"])

    def test_phase_forecast_weights_real_group_counts_and_keeps_decode_load_costs(self):
        sources = [dict(video_id=sid, n_frames=count, physical_end_exact=str(Fraction(count, 4)),
                        normalized_exact_pts=[str(Fraction(i, 4)) for i in range(count)])
                   for sid, count in (("short", 8), ("long", 64))]
        # Four short clips have1group each (8primaryforwards); four long
        # clips have8groups each (36primaryforwards):44total, not8*17.
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            runner.write_adopt(root / "smoke" / "phase" / "completion.json", {
                "ground_model_seconds": 0, "spatial_ground_calls": 0, "spatial_seconds": 0,
                "source_native_frames": 64, "phase_model_seconds_including_reference_qa": 18,
                "phase_primary_forwards": 9, "phase_reference_forwards": 8, "phase_seconds": 20,
                "model_initialization_seconds": 10, "source_duration_exact": "16"})
            assets = {"run_root": directory, "protected_baselines": {"bound": True}}
            baseline = {"40.48": {row["video_id"]: {0: [0, 0, 8]} for row in sources}}
            with patch.object(runner, "enriched_sources", return_value=sources), \
                 patch.object(runner, "baseline_frames", return_value=baseline), \
                 patch.object(runner, "Engine") as model_engine:
                result = runner.forecast(assets)
                model_engine.assert_not_called()
            self.assertEqual(result["phase_clips"], 8)
            self.assertEqual(result["phase_primary_forwards_from_actual_groups"], 44)
            self.assertEqual(result["phase_primary_forward_upper_bound"], 136)
            estimate = result["estimates"]["phase"]
            #18/9*44 modelseconds +2/64*72 decodeCPU =90.25; coldload adds10.
            self.assertAlmostEqual(estimate["temporal_component_seconds"], 90.25)
            self.assertAlmostEqual(estimate["linear_smoke_extrapolation_seconds"], 100.25)
            self.assertAlmostEqual(estimate["planning_with_30pct_margin_seconds"], 100.25 * 1.3)

    def test_semantic_extent_control_is_cpu_only_and_uses_exact_parent_proof(self):
        with tempfile.TemporaryDirectory() as directory:
            engine = runner.Engine.__new__(runner.Engine)
            engine.candidate_id = "g_semantic_extent_control"
            engine.base = {"0": {2: [0, 0, 8]}}
            engine.spatial_config = runner.SpatialConfig()
            evidence_path = Path(directory) / "evidence.json"
            evidence = {"input": "exact_parent_proof"}
            evidence_ref = runner.write_adopt(evidence_path, evidence)
            parent = {"evidence": evidence_ref}
            source = {"video_id": "0"}
            engine.parent_source = Mock(return_value=(parent, {"parent": "checked"}))
            engine._finish_source = Mock(return_value={"completed": True})
            engine.qwen = Mock(side_effect=AssertionError("No model calls allowed"))
            with patch.object(runner, "semantic_extent_control", return_value={
                    "predictions": [{"frame": 2, "bboxes": [1, 1, 6]}],
                    "spatial_evidence": [], "diagnostics": {"no_new_calls": True}}) as derive:
                self.assertEqual(engine.derive_source(source), {"completed": True})
                derive.assert_called_once_with(source, evidence, engine.base["0"], engine.spatial_config)
            engine.qwen.assert_not_called()

    def test_scale_control_keeps_both_centers_exactly_even_at_boundaries(self):
        from improvement.final_sprint_v1.controls import maximum_width_at_fixed_center
        for source, original in [
            ({"width": 1920, "height": 1080, "targetRatioWH": [16, 9]}, [600, 300, 320]),
            ({"width": 1080, "height": 1920, "targetRatioWH": [9, 16]}, [100, 100, 180]),
            ({"width": 1080, "height": 1920, "targetRatioWH": [9, 16]}, [0, 100, 180]),
        ]:
            changed, evidence = maximum_width_at_fixed_center(original, source)
            rw, rh = source["targetRatioWH"]
            def center(box):
                x, y, w = map(Fraction, box)
                return x + w / 2, y + w * rh / (2 * rw)
            self.assertEqual(center(original), center(changed))
            self.assertGreaterEqual(changed[2], original[2])
            self.assertFalse(evidence["center_translation"])
            remaining = Fraction(evidence["maximum_contained_width_exact"]) - changed[2]
            self.assertLess(remaining, 2 * rw)


if __name__ == "__main__":
    unittest.main()
