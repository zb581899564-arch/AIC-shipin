#!/usr/bin/env python3
"""Stdlib-only cost preflight tests. Never loads torch/model/decoder/media."""
from __future__ import annotations

import ast
import copy
import json
from pathlib import Path
import subprocess
import sys
import unittest

from cost_probe import (TimedProcessor, parse_native_pts, prior_gate, source_plan, synthetic_window,
                        validate_admission, validate_config)
from exact_pts import exact_source_pts
from formal_contract import AdmissionRejected, sha256

ROOT = Path(__file__).parent
RUN = ROOT.parent


class CostCpuTests(unittest.TestCase):
    def setUp(self):
        self.config = json.loads((ROOT / "cost_config_32s_v1.json").read_text(encoding="utf-8"))
        self.admission = json.loads((ROOT / "cost_admission_32s_v1.json").read_text(encoding="utf-8"))
        self.source, _ = source_plan(self.config, RUN / "baseline_a/inputs/non_test_frozen8.json")

    def native(self):
        return {"streams": [{"time_base": "1/12800", "avg_frame_rate": "25/1", "width": 534, "height": 300}],
                "frames": [{"best_effort_timestamp": i * 512, "pkt_duration": 512} for i in range(3750)]}

    def test_exact_fixed_plan_and_admission(self):
        validate_config(self.config)
        validate_admission(ROOT / "cost_config_32s_v1.json", self.admission)
        gate = prior_gate(self.admission, RUN)
        self.assertTrue(gate["strict_unknown_gate_reused"])
        self.assertEqual(self.source["source_path"], self.config["selected_source_path"])
        self.assertEqual(self.config["decoder_threads"], 0)

    def test_recipe_changes_and_semantic_inputs_refused(self):
        for name, value in (("updates", 4), ("max_frames", 32), ("window_start_pts", 138.089),
                            ("revision", "main"), ("save_checkpoint", True), ("max_wall_seconds", float("nan")),
                            ("selected_source_sha256", "0" * 64), ("out_dir", "/home/inspur/elsewhere/cost32_01")):
            changed = copy.deepcopy(self.config)
            changed[name] = value
            with self.assertRaises(AdmissionRejected, msg=name):
                validate_config(changed)
        changed = copy.deepcopy(self.config)
        changed["train_semantic_labels"] = "forbidden.jsonl"
        with self.assertRaises(AdmissionRejected):
            validate_config(changed)

    def test_formal_or_truthy_admission_and_wrong_hash_refused(self):
        for name, value in (("formal_c_bce_admitted", True), ("cost_probe_admitted", 1),
                            ("semantic_labels_read", True), ("config_sha256", "0" * 64)):
            changed = copy.deepcopy(self.admission)
            changed[name] = value
            with self.assertRaises(AdmissionRejected):
                validate_admission(ROOT / "cost_config_32s_v1.json", changed)

    def test_native_clock_and_synthetic_grid_replay(self):
        index = parse_native_pts(self.source, self.native())
        self.assertEqual(index["native_time_base"], "1/12800")
        self.assertEqual(index["actual_source_duration_rational"], "150")
        self.assertEqual(index["selected_frame_ids"][:4], [0, 12, 25, 37])
        self.assertEqual(index["selected_exact_pts_rational"][1], "12/25")
        row = synthetic_window(self.source, index, {"path": "not_opened.json", "sha256": "0" * 64})
        self.assertEqual((len(row["frame_ids"]), len(row["grid"])), (64, 16))
        self.assertFalse(row["formal_training_eligible"])
        self.assertEqual([cell["target"] for cell in row["grid"]], [float(i % 2) for i in range(16)])
        self.assertEqual([j for cell in row["grid"] for j in cell["source_frame_ids"]], list(range(800)))

    def test_native_pts_missing_nonzero_origin_duplicate_duration_geometry_refused(self):
        variants = []
        missing = self.native(); del missing["frames"][20]["best_effort_timestamp"]; variants.append(missing)
        origin = self.native(); origin["frames"][0]["best_effort_timestamp"] = 1; variants.append(origin)
        duplicate = self.native(); duplicate["frames"][20]["best_effort_timestamp"] = 19 * 512; variants.append(duplicate)
        duration = self.native(); duration["frames"][20]["pkt_duration"] = 0; variants.append(duration)
        geometry = self.native(); geometry["streams"][0]["width"] = 535; variants.append(geometry)
        for data in variants:
            with self.assertRaises(AdmissionRejected):
                parse_native_pts(self.source, data)

    def test_timing_proxy_preserves_exact_pts_override(self):
        class FakeProcessor:
            def _calculate_timestamps(self, ids, fps, merge_size=2):
                return ["ORIGINAL"]
            def __call__(self):
                return self._calculate_timestamps([0, 12, 25, 37], 25.0, 2)
        underlying = FakeProcessor()
        timed = TimedProcessor(underlying)
        with exact_source_pts(timed, [0, 12, 25, 37], [0.0, .48, 1.0, 1.48], 0.0, 25.0) as record:
            self.assertEqual(timed(), [.24, 1.24])
        self.assertEqual(len(record["processor_calls"]), 1)
        self.assertEqual(underlying._calculate_timestamps([], 1), ["ORIGINAL"])
        self.assertGreaterEqual(timed.last_call_seconds, 0.0)

    def test_plan_cli_no_runtime_imports(self):
        code = ("import sys,cost_probe; sys.argv=['cost_probe.py','--config',sys.argv[1],"
                "'--admission',sys.argv[2],'--plan-only','--metadata-root',sys.argv[3]]; "
                "assert cost_probe.main()==0; assert not ({'torch','transformers','peft','decord'} & set(sys.modules)); "
                "print('NO_RUNTIME_IMPORTS_CONFIRMED')")
        process = subprocess.run([sys.executable, "-c", code, str(ROOT / "cost_config_32s_v1.json"),
            str(ROOT / "cost_admission_32s_v1.json"), str(RUN)], cwd=ROOT, capture_output=True, text=True, encoding="utf-8")
        self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
        self.assertIn("NO_RUNTIME_IMPORTS_CONFIRMED", process.stdout)
        result = json.loads(process.stdout.splitlines()[0])
        self.assertFalse(result["started_runtime"])
        self.assertEqual(result["status"], "PLANNED_COST_ONLY_NO_RUNTIME")

    def test_no_eager_runtime_imports_no_oom_fallback_or_model_merge(self):
        tree = ast.parse((ROOT / "cost_probe.py").read_text(encoding="utf-8"))
        for node in tree.body:
            if isinstance(node, ast.Import):
                self.assertFalse({n.name.split('.')[0] for n in node.names} & {"torch", "transformers", "peft", "decord"})
        source = (ROOT / "cost_probe.py").read_text(encoding="utf-8")
        self.assertNotIn("merge_and_unload", source)
        self.assertNotIn("empty_cache", source)
        self.assertIn("exist_ok=False", source)
        self.assertLess(source.index("torch.cuda.init()"), source.index("import decord"))


if __name__ == "__main__":
    suite = unittest.defaultTestLoader.loadTestsFromTestCase(CostCpuTests)
    result = unittest.TextTestRunner(verbosity=2).run(suite)
    report = {"status": "PASS_CPU_COST_CONTRACT_ONLY" if result.wasSuccessful() else "FAIL_CPU_COST_CONTRACT",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "real_media_read": False, "runtime_loaded": False, "real_gpu_run": False}
    (ROOT / "cost_cpu_test_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
