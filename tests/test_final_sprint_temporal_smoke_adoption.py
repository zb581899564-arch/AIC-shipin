"""Metadata adoption tests with synthetic426 identities; no inference or render."""
from copy import deepcopy
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from improvement.final_sprint_v1 import temporal_smoke_adoption as adoption
from improvement.final_sprint_v1.contracts import ref, save_new, stable_key, strict_load
from improvement.final_sprint_v1.frozen_field import _binding


class TemporalSmokeAdoptionTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.addCleanup(self.temporary.cleanup)
        self.root = Path(self.temporary.name)

    def write(self, name, value):
        return save_new(self.root / (name + ".json"), value)

    def receipt(self, name, count, weight, provenance=None):
        value = dict(schema="AIC_FINAL_PARAMETERS_V1", origin="actual_loaded", component_id=name,
                     quantization_does_not_reduce_parameters=True, total_elements=count, weight_files=[weight],
                     tensors=[dict(name=name, shape=[count], elements=count,
                                   source=dict(weight_sha256=weight["sha256"], tensor_name=name))])
        if provenance is not None:
            value["baseline_provenance"] = provenance
        return self.write(name + "_receipt", value)

    def fixture(self, family="specialist"):
        baselines = {name: self.write("baseline" + name, {"synthetic": name}) for name in ("40.48", "40.47")}
        auxiliary_counts = dict(original_time=10_000_000, semantic_residual=10_000_000, i3d=10_000_000, sport_umt=19_686_250)
        weights = {name: self.write(name + "_weight", {"synthetic": name}) for name in auxiliary_counts}
        provenance = dict(schema="AIC_FINAL_BASELINE_DEPENDENCIES_V1", protected_baselines=baselines,
                          checkpoint_refs=weights, registration_refs={"config": self.write("config", {})})
        auxiliary_refs = [self.receipt(name, count, weights[name], provenance) for name, count in auxiliary_counts.items()]
        completion = self.write("auxiliary_completion", dict(schema="AIC_FINAL_BOOTSTRAP_INVENTORY_COMPLETION_V1",
            baseline_provenance=provenance, parameter_receipts=auxiliary_refs))
        model_counts = dict(qwen_base=8_767_123_696)
        if family == "specialist":
            model_counts.update(clip_vit_b32=151_277_313, cg_detr=12_021_035)
        model_refs = [self.receipt(name, count, self.write(name + "_weight", {"synthetic": name})) for name, count in model_counts.items()]
        clock = self.write("clock", {"synthetic": "native clock identities"})
        sources = [dict(video_id=str(index), n_frames=2, media=self.write("media" + str(index), {"synthetic": index}),
                        clock=dict(clock, source_key=str(index))) for index in range(426)]
        old = dict(sources=sources, protected_baselines=baselines, source_commit={"commit": "b" * 40})
        old_ref = self.write("old_assets", old)
        packet_refs, entries = [], {}
        for prefix in (("phase_",) if family == "phase" else ("query_", "clip_features_", "specialist_source_")):
            identity = self.write(prefix + "packet", {"synthetic": prefix})
            packet_refs.append(identity)
            entries[prefix + "0"] = dict(returned=identity, call_binding={"source": sources[0]["media"]})
        wrapper = self.root / "old_wrapper"
        wrapper.mkdir()
        command = ["python", "-m", "improvement.final_sprint_v1.cli", "smoke", "--assets", old_ref["path"],
                   "--expected-commit", old["source_commit"]["commit"], "--candidate", "r_phase_event" if family == "phase" else "m_specialist"]
        save_new(wrapper / "claim.json", dict(wrapper_id="fixed-owner", asset_lock=old_ref, command=command))
        wrapper_value = dict(schema="AIC_FINAL_OWNED_WRAPPER_V1", owned_wrapper_id="fixed-owner", asset_lock=old_ref,
            work_terminated=True, no_external_task_signaled=True, termination_basis="owned_wrapper_terminal",
            stopped_owned_process=False, stop_reason=None, child_exit_code=0)
        wrapper_ref = save_new(wrapper / "completion.json", wrapper_value)
        manifest = self.write("adoption_manifest", {"parents": [{"old_assets": old_ref, "wrapper": wrapper_ref}]})
        prior = dict(status="REAL_ENGINEERING_SMOKE_PASS", binding=dict(asset_lock=old_ref, code=old["source_commit"], family=family),
            source_sha256=sources[0]["media"]["sha256"], source_native_frames=2, source_duration_exact="24",
            evidence_refs=packet_refs, parameter_receipts=model_refs, phase_seconds=8.0 if family == "phase" else 0.0,
            specialist_seconds=10.0 if family == "specialist" else 0.0, model_initialization_seconds=50.0,
            spatial_seconds=60.0, spatial_frames=16, spatial_ground_calls=2, ground_model_seconds=58.0,
            phase_model_seconds_including_reference_qa=7.0, phase_primary_forwards=2, phase_reference_forwards=8,
            phase_clips=1, accounting={"historical_wall_seconds": 133.5})
        prior_ref = self.write("old_smoke", prior)
        assets = dict(run_root=str(self.root / "new_run"), source_commit={"commit": "a" * 40}, sources=deepcopy(sources),
            protected_baselines=baselines, baseline_parameter_receipts=auxiliary_refs,
            baseline_registration_provenance=provenance, baseline_inventory_completion=completion,
            adopted_inputs={"package_inputs": self.write("package_inputs", {})},
            temporal_smoke_adoption=dict(old_assets=old_ref, smoke_receipt=prior_ref, wrapper=str(wrapper)))
        assets["phase_call_adoption" if family == "phase" else "pure_call_adoption"] = manifest
        binding = _binding(assets)
        spec_ref = self.write("field_spec", {"asset_binding": binding})
        cache_sources = {source["video_id"]: dict(support=[0, 1], boxes={"0": [0, 0, 10], "1": [1, 0, 10]},
                                                  native_pts={"0": "0", "1": "1"}) for source in sources}
        cache_ref = self.write("field_cache", dict(schema="AIC_FROZEN_SPATIAL_FIELD_CACHE_V1", spec_sha256=stable_key({"asset_binding": binding}), sources=cache_sources))
        metadata = dict(field_frames=852, native_frames=852, new_model_calls=0, new_media_decodes=0,
            unsupported_policy="UNKNOWN_NO_BOX_NO_ACTION", baseline_overlap={name: dict(all_frames_supported=True, all_boxes_exact=True) for name in baselines},
            sources={source["video_id"]: dict(source_sha256=source["media"]["sha256"], native_frames=2,
                supported_frames=2, all_supported_native_pts_equal=True) for source in sources})
        metadata_ref = self.write("field_metadata", metadata)
        assets["frozen_spatial_field"] = self.write("field_receipt", dict(schema="AIC_FROZEN_SPATIAL_FIELD_RECEIPT_V1",
            status="CPU_FIELD_RENDERED_DOMAIN_LOCKED", asset_binding=binding, spec_ref=spec_ref, cache_ref=cache_ref, metadata_ref=metadata_ref))
        assets_path = self.write("new_assets", assets)["path"]
        candidate = "r_time_event" if family == "phase" else "m_time_event"
        registry = {"candidates": {candidate: dict(implementation_status="IMPLEMENTED", configuration={"spatial_policy": adoption.POLICY})}}
        return assets, assets_path, candidate, registry, entries, prior

    def smoke(self, fixture):
        assets, path, candidate, registry, entries, _ = fixture
        module = "phase_call_adoption" if candidate.startswith("r_") else "pure_call_adoption"
        with patch.object(adoption.asset_api, "candidate_registry", return_value=registry), \
             patch("improvement.final_sprint_v1." + module + ".validate_manifest", return_value=entries), \
             patch.object(adoption, "atomic_new", side_effect=save_new):
            return adoption.smoke(assets, path, candidate)

    def test_specialist_actual_inventory_plus_four_auxiliaries_and_zero_new_spatial_gpu(self):
        fixture = self.fixture()
        result = self.smoke(fixture)
        self.assertEqual(result["actual_parameters"], 8_980_108_294)
        self.assertEqual(result["specialist_seconds"], 10.0)
        self.assertEqual(result["model_initialization_seconds"], 50.0)
        self.assertEqual(result["cpu_field_validated_sources"], 426)
        self.assertEqual(result["cpu_field_validated_frames"], 852)
        self.assertEqual(result["new_gpu_model_calls"], 0)
        self.assertTrue(all(result[key] == 0 for key in ("spatial_seconds", "spatial_ground_calls", "ground_model_seconds", "spatial_frames")))
        self.assertFalse((Path(fixture[0]["run_root"]) / "model_parameters").exists())
        self.assertEqual(self.smoke(fixture), result)

    def test_phase_keeps_original_first_reference_qa_and_full_parameter_union(self):
        result = self.smoke(self.fixture("phase"))
        self.assertEqual(result["actual_parameters"], 8_816_809_946)
        self.assertEqual(result["phase_seconds"], 8.0)
        self.assertEqual(result["phase_reference_forwards"], 8)
        self.assertEqual(result["new_independent_reference_forwards"], 0)
        self.assertEqual(result["phase_model_seconds_including_reference_qa"], 7.0)

    def test_unknown_or_nonuniform_candidate_rejected(self):
        fixture = self.fixture()
        fixture[3]["candidates"][fixture[2]]["configuration"]["spatial_policy"] = "fallback_when_failed"
        with self.assertRaisesRegex(ValueError, "uniform frozen-field"):
            self.smoke(fixture)

    def test_original_smoke_must_be_an_explicit_audited_parent(self):
        fixture = self.fixture()
        fixture[0]["pure_call_adoption"] = self.write("wrong_manifest", {"parents": []})
        with self.assertRaisesRegex(ValueError, "outside explicit audited"):
            self.smoke(fixture)

    def test_missing_actual_auxiliary_inventory_rejected(self):
        fixture = self.fixture()
        fixture[0]["baseline_parameter_receipts"] = fixture[0]["baseline_parameter_receipts"][:-1]
        with self.assertRaises(ValueError):
            self.smoke(fixture)

    def test_foreign_smoke_input_is_rejected(self):
        fixture = self.fixture()
        fixture[0]["sources"][0]["clock"] = dict(fixture[0]["sources"][0]["clock"], source_key="foreign")
        with self.assertRaisesRegex(ValueError, "smoke/input binding"):
            self.smoke(fixture)

    def test_failed_or_stopped_wrapper_is_not_actual_natural_smoke_authority(self):
        fixture = self.fixture()
        original = Path(fixture[0]["temporal_smoke_adoption"]["wrapper"])
        invalid = self.root / "invalid_wrapper"
        invalid.mkdir()
        save_new(invalid / "claim.json", strict_load(original / "claim.json"))
        terminal = strict_load(original / "completion.json")
        terminal["child_exit_code"] = 1
        save_new(invalid / "completion.json", terminal)
        fixture[0]["temporal_smoke_adoption"]["wrapper"] = str(invalid)
        with self.assertRaisesRegex(ValueError, "naturally successful owned wrapper"):
            self.smoke(fixture)


if __name__ == "__main__":
    unittest.main()
