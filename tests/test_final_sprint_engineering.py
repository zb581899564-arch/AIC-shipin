"""Synthetic CPU engineering checks; no real media/model or quality validation."""
from __future__ import annotations

import copy
import json
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch
import zipfile
from types import SimpleNamespace

from improvement.final_sprint_v1.contracts import (
    atomic_new, checked, inspect_loaded_parameters, native_clock, ref, save_new, stable_key,
    strict_load, strict_loads, total_parameters, validate_sources)
from improvement.final_sprint_v1.packaging import (
    _candidate_contract, build_package, prediction_identity, verify_transfer)
from improvement.final_sprint_v1.state import TaskStore, UnresolvedClaim


class Fixture:
    def __init__(self, root):
        self.root = root
        self.sources = []
        clocks = {}
        for sid in ("0", "1"):
            media = root / (sid + ".media")
            media.write_bytes(("synthetic-source-" + sid).encode())
            self.sources.append({"video_id": sid, "media": ref(media), "width": 100, "height": 80,
                "n_frames": 3, "targetRatioWH": [1, 1], "index_row": {
                    "video_id": sid, "targetRatioWH": [1, 1], "video_file": sid + ".mp4"}})
            clocks[sid] = {"source_sha256": ref(media)["sha256"],
                           "normalized_exact_pts": ["0", "1/30", "2/30"], "physical_end_exact": "1/10"}
        clock_ref = save_new(root / "clocks.json", clocks)
        for source in self.sources:
            source["clock"] = {**clock_ref, "source_key": source["video_id"]}
        self.baselines = {}
        for name, frame in (("40.48", 0), ("40.47", 1)):
            rows = [{"video_id": sid, "targetRatioWH": [1, 1],
                     "predictions": [{"frame": frame, "bboxes": [0, 0, 50]}]} for sid in ("0", "1")]
            path = root / (name + ".zip")
            with zipfile.ZipFile(path, "w") as archive:
                archive.writestr("predictions.jsonl", "".join(json.dumps(row) + "\n" for row in rows))
            self.baselines[name] = ref(path)
        weights = root / "tiny.weights"
        weights.write_bytes(b"synthetic model identity")
        weight_ref = ref(weights)
        inventory = {"schema": "AIC_FINAL_PARAMETERS_V1", "origin": "actual_loaded",
            "component_id": "tiny", "weight_files": [weight_ref],
            "quantization_does_not_reduce_parameters": True, "total_elements": 10,
            "tensors": [{"name": "tiny", "shape": [10], "elements": 10, "aliases": ["tiny"],
                         "source": {"weight_sha256": weight_ref["sha256"], "tensor_name": "tiny"}}]}
        self.parameters = [save_new(root / "parameters.json", inventory)]
        self.binding = {"synthetic_test_only": True, "required_model_components": ["tiny"],
                        "protected_baselines": self.baselines, "code": "synthetic-contract-test"}
        frames = [{"frame": 0, "bboxes": [10, 5, 50]}]
        evidence = {"schema": "AIC_FINAL_SPATIAL_EVIDENCE_V1", "video_id": "0",
            "source_sha256": self.sources[0]["media"]["sha256"], "frames": frames,
            "binding_sha256": stable_key(self.binding), "model_components": ["tiny"],
            "input_refs": [self.sources[0]["media"]], "algorithm": "synthetic_test_only"}
        proof = save_new(root / "spatial_evidence.json", evidence)
        empty_evidence = dict(evidence, video_id="1", frames=[],
            source_sha256=self.sources[1]["media"]["sha256"], input_refs=[self.sources[1]["media"]])
        empty_proof = save_new(root / "empty_source_evidence.json", empty_evidence)
        self.results = [
            {"video_id": "0", "source_sha256": self.sources[0]["media"]["sha256"],
             "status": "SUCCESS_NONEMPTY", "predictions": frames,
             "binding_sha256": stable_key(self.binding), "evidence": proof,
             "spatial_provenance": [{"frame": 0, "kind": "grounded", "evidence": proof,
                                     "source_sha256": self.sources[0]["media"]["sha256"]}]},
            {"video_id": "1", "source_sha256": self.sources[1]["media"]["sha256"],
             "binding_sha256": stable_key(self.binding), "evidence": empty_proof,
             "status": "SUCCESS_EMPTY", "predictions": [], "spatial_provenance": []}]

    def package(self, candidate="a", output=None, **kwargs):
        options = dict(candidate_id=candidate, sources=self.sources, source_results=self.results,
            parameter_receipts=self.parameters, protected_baselines=self.baselines, binding=self.binding,
            output_dir=output or self.root / candidate, history_path=self.root / "history.jsonl", expected_count=2)
        options.update(kwargs)
        return build_package(**options)


class ContractTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)

    def tearDown(self):
        self.temporary.cleanup()

    def test_strict_nonfinite_duplicate_and_huge_exponent_rejected(self):
        for value in ('{"a":1,"a":2}', '{"a":NaN}', '{"a":1e999}', '{"a":Infinity}'):
            with self.assertRaises(ValueError):
                strict_loads(value)

    def test_asset_mutation_invalidates_process_hash_cache(self):
        path = self.root / "x"
        path.write_bytes(b"abc")
        identity = ref(path)
        checked(identity)
        path.write_bytes(b"abd")
        with self.assertRaisesRegex(ValueError, "SHA256"):
            checked(identity)

    def test_recent_large_file_with_coarse_stat_is_rehashed(self):
        path = self.root / "recent-large"
        payload = b"a" * ((1 << 20) + 1)
        path.write_bytes(payload)
        identity = ref(path)
        original_stat = Path.stat
        frozen_stat = path.stat()

        def coarse_stat(candidate, *args, **kwargs):
            if candidate == path:
                return frozen_stat
            return original_stat(candidate, *args, **kwargs)

        tick_now = max(frozen_stat.st_mtime_ns, frozen_stat.st_ctime_ns) + 1_000_000_000
        with patch.object(Path, "stat", coarse_stat), patch(
                "improvement.final_sprint_v1.contracts.time.time_ns", return_value=tick_now):
            checked(identity)
            path.write_bytes(b"b" * len(payload))
            with self.assertRaisesRegex(ValueError, "SHA256"):
                checked(identity)

    def test_complete_aggregate_native_clock_and_bad_source_key(self):
        fixture = Fixture(self.root)
        clocks = validate_sources(fixture.sources, expected_count=2)
        self.assertEqual(str(clocks["0"][0][1]), "1/30")
        fixture.sources[0]["clock"]["source_key"] = "1"
        with self.assertRaisesRegex(ValueError, "source key"):
            validate_sources(fixture.sources, expected_count=2)

    def test_missing_clock_frame_and_rounded_pts_fail(self):
        fixture = Fixture(self.root)
        path = self.root / "badclock.json"
        clock = {"source_sha256": fixture.sources[0]["media"]["sha256"],
                 "normalized_exact_pts": [0, 0.03, 0.06], "physical_end_exact": "1/10"}
        fixture.sources[0]["clock"] = save_new(path, clock)
        with self.assertRaisesRegex(ValueError, "exact rationals"):
            validate_sources(fixture.sources, expected_count=2)

    def test_original_pts_origin_and_positive_terminal_witness_cannot_disagree(self):
        clock = {"source_sha256": "a" * 64, "normalized_exact_pts": ["0", "1/30"],
                 "physical_end_exact": "1/15", "first_original_pts_exact": "-1/10",
                 "original_exact_pts": ["-1/10", "-1/15"],
                 "physical_endpoint_evidence": {"kind": "LAST_NATIVE_FRAME_PTS_PLUS_POSITIVE_DURATION",
                     "last_normalized_pts_exact": "1/30", "last_frame_duration_exact": "1/30"}}
        native_clock(clock, "a" * 64)
        bad_origin = copy.deepcopy(clock)
        bad_origin["first_original_pts_exact"] = "0"
        with self.assertRaisesRegex(ValueError, "origin/normalization"):
            native_clock(bad_origin, "a" * 64)
        bad_end = copy.deepcopy(clock)
        bad_end["physical_endpoint_evidence"]["last_frame_duration_exact"] = "1/15"
        with self.assertRaisesRegex(ValueError, "native-duration witness"):
            native_clock(bad_end, "a" * 64)

    def test_parameter_sharing_is_tensor_identity_not_whole_model(self):
        fixture = Fixture(self.root)
        old = strict_load(fixture.parameters[0]["path"])
        other = copy.deepcopy(old)
        other["component_id"] = "second_view"
        # Same shared base plus a new adapter tensor adds only that tensor.
        other["tensors"].append({"name": "adapter", "shape": [4], "elements": 4, "aliases": ["adapter"],
            "source": {"weight_sha256": old["weight_files"][0]["sha256"], "tensor_name": "adapter"}})
        other["total_elements"] = 14
        references = fixture.parameters + [save_new(self.root / "other.json", other)]
        counted = total_parameters(references)
        self.assertEqual(counted["total_elements"], 14)
        self.assertEqual(counted["distinct_tensors"], 2)

    def test_different_weight_identity_cannot_share_and_over_budget_fails(self):
        fixture = Fixture(self.root)
        value = strict_load(fixture.parameters[0]["path"])
        value["tensors"][0]["shape"] = [9_000_000_001]
        value["tensors"][0]["elements"] = value["total_elements"] = 9_000_000_001
        with self.assertRaisesRegex(ValueError, "exceed 9B"):
            total_parameters([save_new(self.root / "huge.json", value)])

    def test_loaded_inventory_counts_ties_once_and_logical_quantized_size(self):
        class Parameter:
            def __init__(self, shape, address, quant_shape=None):
                self.shape = shape
                self.device = SimpleNamespace(type="cpu", index=None)
                self.dtype = "uint8" if quant_shape else "float32"
                self.address = address
                self.quant_state = SimpleNamespace(shape=quant_shape) if quant_shape else None
            def numel(self):
                import math
                return math.prod(self.shape)
            def storage_offset(self):
                return 0
            def untyped_storage(self):
                return SimpleNamespace(data_ptr=lambda: self.address)
        tied, packed = Parameter((2, 3), 123), Parameter((8,), 456, (4, 4))
        class Module:
            def named_parameters(self, remove_duplicate=False):
                return [("embed", tied), ("head", tied), ("packed", packed)]
        path = self.root / "w"
        path.write_bytes(b"fixture")
        receipt = inspect_loaded_parameters(Module(), "test", [ref(path)])
        self.assertEqual(receipt["total_elements"], 22)
        self.assertEqual(receipt["tensors"][0]["aliases"], ["embed", "head"])


class ResumeTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.store = TaskStore(self.root / "run")
        self.binding = {"assets_sha": "exact-assets", "config_sha": "exact-config"}

    def tearDown(self):
        self.temporary.cleanup()

    def test_durable_success_adopted_even_without_terminal_marker(self):
        claim = self.store.claim("source0", self.binding)
        artifact = save_new(self.root / "result.json", {"native": [1]})
        claim.complete({"result": artifact}, {"accounting": {"gpu_seconds": 12}})
        (claim.directory / "completion.json").unlink()  # Synthetic crash window.
        reused = self.store.claim("source0", self.binding)
        self.assertTrue(reused.reused)
        self.assertEqual(reused.result["artifacts"]["result"], artifact)
        self.assertTrue((claim.directory / "completion.json").exists())
        self.assertEqual((self.store.root / "ledger.jsonl").read_text().count('"event":"SUCCESS"'), 1)

    def test_success_artifact_changed_cannot_trigger_silent_rerun(self):
        claim = self.store.claim("source0", self.binding)
        artifact = save_new(self.root / "result.json", {"native": [1]})
        claim.complete({"result": artifact})
        Path(artifact["path"]).write_text('{}')
        with self.assertRaises(ValueError):
            self.store.claim("source0", self.binding)

    def test_torn_ledger_does_not_block_adoption_or_invent_repeat_work(self):
        claim = self.store.claim("source0", self.binding)
        artifact = save_new(self.root / "result.json", {"native": [1]})
        claim.complete({"result": artifact}, {"accounting": {"gpu_seconds": 12}})
        ledger = self.store.root / "ledger.jsonl"
        original = ledger.read_bytes() + b'{"event":"SUCC'
        ledger.write_bytes(original)  # Inject a torn subsequent log write.
        reused = self.store.claim("source0", self.binding)
        self.assertTrue(reused.reused)
        self.assertEqual(reused.result["artifacts"]["result"], artifact)
        self.assertEqual(ledger.read_text().count('"event":"SUCCESS"'), 1)
        archives = list((self.store.root / "ledger_recovery").glob("interrupted_*.jsonl"))
        self.assertEqual(len(archives), 1)
        self.assertEqual(archives[0].read_bytes(), original)

    def test_claim_without_terminal_does_not_restart_from_old_pid(self):
        claim = self.store.claim("source0", self.binding)
        with self.assertRaises(UnresolvedClaim):
            self.store.claim("source0", self.binding)
        self.assertFalse((claim.directory / "success.json").exists())

    def test_failed_attempt_requires_exact_owned_wrapper_terminal(self):
        claim = self.store.claim("source0", self.binding)
        claim.fail(RuntimeError("targeted smoke failure"), accounting={"gpu_seconds": 2})
        with self.assertRaises(UnresolvedClaim):
            self.store.claim("source0", self.binding)
        evidence = save_new(self.root / "terminal.json", {"task_id": "source0", "work_terminated": True,
            "no_external_task_signaled": True, "claim_sha256": ref(claim.directory / "claim.json")["sha256"],
            "termination_basis": "owned_wrapper_terminal"})
        self.store.resolve_interrupted("source0", self.binding, evidence)
        retried = self.store.claim("source0", self.binding)
        self.assertFalse(retried.reused)
        self.assertNotEqual(retried.directory, claim.directory)
        self.assertTrue((claim.directory / "failure.json").exists())

    def test_reuse_with_different_config_is_rejected(self):
        self.store.claim("source0", self.binding)
        with self.assertRaisesRegex(ValueError, "different assets/code/config"):
            self.store.claim("source0", {"assets_sha": "changed"})


class PackageTests(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.fixture = Fixture(self.root)

    def tearDown(self):
        self.temporary.cleanup()

    def test_real_artifact_checks_and_exact_idempotent_readback(self):
        result = self.fixture.package()
        self.assertEqual(result["status"], "SYNTHETIC_TEST_ONLY")
        self.assertFalse(result["offline_quality_validated"])
        again = self.fixture.package()
        self.assertEqual(again, result)
        transferred = self.root / "received.zip"
        transferred.write_bytes(Path(result["zip_ref"]["path"]).read_bytes())
        self.assertEqual(verify_transfer(result, transferred)["status"], "TRANSFER_IDENTICAL")
        with zipfile.ZipFile(transferred) as archive:
            rows = [json.loads(line) for line in archive.read("predictions.jsonl").splitlines()]
        self.assertEqual(rows[0]["video_file"], "0.mp4")
        self.assertEqual(rows[1]["predictions"], [])

    def test_torn_own_package_write_is_preserved_and_rebuilt_without_inference(self):
        output = self.root / "a"
        output.mkdir()
        torn_jsonl = output / "predictions.jsonl.PENDING"
        torn_zip = output / "candidate_FINAL_A.zip.PENDING"
        torn_jsonl.write_bytes(b'{"video_id":')
        torn_zip.write_bytes(b"PK\\x03")
        result = self.fixture.package()
        leftovers = sorted(output.glob("*.PENDING.interrupted-*"))
        self.assertEqual(len(leftovers), 2)
        self.assertEqual({p.read_bytes() for p in leftovers}, {b'{"video_id":', b"PK\\x03"})
        self.assertEqual(result["status"], "SYNTHETIC_TEST_ONLY")
        self.assertEqual(self.fixture.package(), result)

    def test_failed_source_is_not_legal_empty(self):
        self.fixture.results[1]["status"] = "FAILED"
        with self.assertRaisesRegex(ValueError, "Failed/incomplete"):
            self.fixture.package()

    def test_missing_source_and_false_empty_terminal_fail(self):
        with self.assertRaisesRegex(ValueError, "Missing/extra"):
            self.fixture.package(source_results=self.fixture.results[:1])
        self.fixture.results[1]["status"] = "SUCCESS_NONEMPTY"
        with self.assertRaisesRegex(ValueError, "terminal contradicts"):
            self.fixture.package()

    def test_frame_shape_or_proof_forgery_rejected(self):
        self.fixture.results[0]["predictions"][0]["bboxes"] = [11, 5, 50]
        with self.assertRaisesRegex(ValueError, "actual frame-specific"):
            self.fixture.package()

    def test_outside_frame_ratio_bbox_rejected_without_epsilon(self):
        self.fixture.results[0]["predictions"][0]["bboxes"] = [10, 30.00000001, 50]
        with self.assertRaisesRegex(ValueError, "leaves the original frame"):
            self.fixture.package()

    def test_duplicate_frame_and_non_native_frame_fail(self):
        self.fixture.results[0]["predictions"].append(copy.deepcopy(self.fixture.results[0]["predictions"][0]))
        with self.assertRaisesRegex(ValueError, "sorted unique native"):
            self.fixture.package()

    def test_all_empty_not_submitted(self):
        for result in self.fixture.results:
            result.update(status="SUCCESS_EMPTY", predictions=[], spatial_provenance=[])
            evidence = strict_load(result["evidence"]["path"])
            evidence["frames"] = []
            result["evidence"] = save_new(self.root / (result["video_id"] + "_empty_evidence.json"), evidence)
        with self.assertRaisesRegex(ValueError, "ALL_EMPTY"):
            self.fixture.package()

    def test_all_selected_not_submitted(self):
        for source, result in zip(self.fixture.sources, self.fixture.results):
            frames = [{"frame": i, "bboxes": [10, 5, 50]} for i in range(3)]
            evidence = {"schema": "AIC_FINAL_SPATIAL_EVIDENCE_V1", "video_id": source["video_id"],
                "source_sha256": source["media"]["sha256"], "frames": frames,
                "binding_sha256": stable_key(self.fixture.binding), "model_components": ["tiny"],
                "input_refs": [source["media"]], "algorithm": "synthetic_test_only"}
            proof = save_new(self.root / (source["video_id"] + ".proof.json"), evidence)
            result.update(status="SUCCESS_NONEMPTY", predictions=frames, evidence=proof, spatial_provenance=[
                {"frame": i, "kind": "grounded", "evidence": proof,
                 "source_sha256": source["media"]["sha256"]} for i in range(3)])
        with self.assertRaisesRegex(ValueError, "ALL_SELECTED"):
            self.fixture.package()

    def test_legal_empty_still_requires_exact_candidate_and_input_proof(self):
        empty = self.fixture.results[1]
        old_binding = empty["binding_sha256"]
        empty["binding_sha256"] = "f" * 64
        with self.assertRaisesRegex(ValueError, "different exact candidate binding"):
            self.fixture.package()
        empty["binding_sha256"] = old_binding
        empty["evidence"] = self.fixture.results[0]["evidence"]
        with self.assertRaisesRegex(ValueError, "Spatial proof"):
            self.fixture.package()
        del empty["evidence"]
        with self.assertRaisesRegex(ValueError, "including empty"):
            self.fixture.package()

    def test_identical_prediction_under_new_name_rejected(self):
        self.fixture.package("a")
        with self.assertRaisesRegex(ValueError, "DUPLICATE_CANDIDATE"):
            self.fixture.package("b")

    def test_numerically_identical_int_float_boxes_not_novel(self):
        rows = [{"video_id": "0", "targetRatioWH": [1, 1],
                 "predictions": [{"frame": 0, "bboxes": [10, 5, 50]}]}]
        other = copy.deepcopy(rows)
        other[0]["model_params_b"] = 8.5
        other[0]["predictions"][0]["bboxes"] = [10.0, 5.0, 50.0]
        self.assertEqual(prediction_identity(rows), prediction_identity(other))

    def test_missing_auxiliary_inventory_blocks_package(self):
        self.fixture.binding["required_model_components"].append("missing_aux")
        with self.assertRaisesRegex(ValueError, "lacks actual parameter"):
            self.fixture.package()

    def test_g_geometry_candidate_must_keep_every_protected_temporal_frame(self):
        rows = [{"video_id": "0", "targetRatioWH": [1, 1],
                 "predictions": [{"frame": 0, "bboxes": [10, 5, 50]}]}]
        baseline = copy.deepcopy(rows)
        baseline[0]["predictions"][0]["bboxes"] = [0, 0, 70]
        binding = {"candidate": {"selection": "protected40.48"}}
        _candidate_contract("g_semantic_extent_control", binding, rows, {"40.48": baseline})
        changed = copy.deepcopy(rows)
        changed[0]["predictions"][0]["frame"] = 1
        with self.assertRaisesRegex(ValueError, "G_TEMPORAL_DRIFT"):
            _candidate_contract("g_subject", binding, changed, {"40.48": baseline})
        with self.assertRaisesRegex(ValueError, "explicitly bind"):
            _candidate_contract("g_subject", {}, rows, {"40.48": baseline})

    def test_native_source_identity_not_optional(self):
        del self.fixture.results[0]["source_sha256"]
        with self.assertRaisesRegex(ValueError, "source media identity"):
            self.fixture.package()


if __name__ == "__main__":
    unittest.main()
