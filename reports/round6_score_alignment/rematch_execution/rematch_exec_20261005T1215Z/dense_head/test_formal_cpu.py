#!/usr/bin/env python3
"""Stdlib CPU/AST tests: current data STOP cannot load any training runtime."""
from __future__ import annotations

import ast
import json
from pathlib import Path
import subprocess
import sys
import tempfile
import unittest

from exact_pts import exact_source_pts
from formal_contract import AdmissionRejected, PASS_DATA_STATUS, admit, sha256, train_bound_file, validate_config

ROOT = Path(__file__).parent


class FormalCpuTests(unittest.TestCase):
    def test_false_missing_and_truthy_integer_admission_refuse_first(self):
        with tempfile.TemporaryDirectory(prefix="formal_contract_test_", dir=ROOT) as task_dir:
            directory = Path(task_dir)
            path = directory / "admission.json"
            for value in (None, False, 1):
                path.write_text(json.dumps({"formal_c_bce_admitted": value}), encoding="utf-8")
                with self.assertRaisesRegex(AdmissionRejected, "explicitly true"):
                    admit(path, directory / "CONFIG_MUST_NOT_BE_OPENED.json")

    def test_actual_current_stop_refuses_before_any_config_manifest_runtime(self):
        gate_path = ROOT.parent / "data_audit" / "gate_decision.json"
        self.assertTrue(gate_path.is_file())
        with tempfile.TemporaryDirectory(prefix="formal_contract_test_", dir=ROOT) as task_dir:
            directory = Path(task_dir)
            path = directory / "admission.json"
            path.write_text(json.dumps({"schema": "aic_dense_formal_admission_v1", "scope": "FORMAL_C_TRAIN_ONLY",
                "formal_c_bce_admitted": True, "data_gate": {"path": str(gate_path), "sha256": sha256(gate_path)}}), encoding="utf-8")
            with self.assertRaisesRegex(AdmissionRejected, "STOP_C_FORMAL_BCE_UNKNOWN_NEGATIVE_SEMANTICS"):
                admit(path, directory / "CONFIG_MUST_NOT_BE_OPENED.json")
            code = ("import sys; import train_dense; "
                    "sys.argv=['train_dense.py','--admission',sys.argv[1],'--config',sys.argv[2]]; "
                    "result=train_dense.main(); "
                    "assert result==1; "
                    "assert not ({'torch','transformers','peft','decord'} & set(sys.modules)); "
                    "print('NO_RUNTIME_IMPORTS_CONFIRMED')")
            process = subprocess.run([sys.executable, "-c", code, str(path),
                                      str(directory / "CONFIG_MUST_NOT_BE_OPENED.json")], cwd=ROOT,
                                     capture_output=True, text=True, encoding="utf-8")
            self.assertEqual(process.returncode, 0, process.stdout + process.stderr)
            self.assertIn("NO_RUNTIME_IMPORTS_CONFIRMED", process.stdout)
            report = json.loads(process.stdout.splitlines()[0])
            self.assertFalse(report["started_runtime"])

    def test_zero_negative_supervision_refuses_before_config(self):
        with tempfile.TemporaryDirectory(prefix="formal_contract_test_", dir=ROOT) as task_dir:
            directory = Path(task_dir)
            gate = directory / "gate.json"
            gate.write_text(json.dumps({"status": PASS_DATA_STATUS, "formal_c_bce_admitted": True,
                "complete_observation_status": "PASS", "generic_highlight_negative_semantics_status": "PASS",
                "usage_basis_status": "PASS", "teacher_negative_rows": 0,
                "verified_observation_rows": 704, "known_negative_frame_count": 0}), encoding="utf-8")
            admission = directory / "admission.json"
            admission.write_text(json.dumps({"schema": "aic_dense_formal_admission_v1", "scope": "FORMAL_C_TRAIN_ONLY",
                "formal_c_bce_admitted": True, "data_gate": {"path": str(gate), "sha256": sha256(gate)}}), encoding="utf-8")
            with self.assertRaisesRegex(AdmissionRejected, "teacher_negative_rows"):
                admit(admission, directory / "CONFIG_MUST_NOT_BE_OPENED.json")

    def test_non_train_manifest_roles_rejected_before_open(self):
        for name in ("confirm_temporal.jsonl", "dev_temporal.jsonl", "dense_train_test.jsonl"):
            with self.assertRaises(AdmissionRejected):
                train_bound_file({"path": str(ROOT / name), "split": "train", "sha256": "0" * 64}, "forbidden")
        with self.assertRaises(AdmissionRejected):
            train_bound_file({"path": str(ROOT / "train_temporal.jsonl"), "split": "confirm", "sha256": "0" * 64}, "forbidden")

    def test_no_optimizer_defaults_and_no_eager_training_stack(self):
        with self.assertRaises(AdmissionRejected):
            validate_config({"schema": "aic_dense_formal_run_v1", "run_id": "test"})
        for name in ("formal_contract.py", "exact_pts.py", "train_dense.py"):
            tree = ast.parse((ROOT / name).read_text(encoding="utf-8"))
            for node in tree.body:
                if isinstance(node, ast.Import):
                    self.assertFalse({alias.name.split(".")[0] for alias in node.names} & {"torch", "transformers", "peft", "decord"})
                if isinstance(node, ast.ImportFrom):
                    self.assertNotIn(node.module.split(".")[0], {"torch", "transformers", "peft", "decord", "dense_time", "probe_8b"})
        tree = ast.parse((ROOT / "train_dense.py").read_text(encoding="utf-8"))
        main = next(node for node in tree.body if isinstance(node, ast.FunctionDef) and node.name == "main")
        calls = [node for node in ast.walk(main) if isinstance(node, ast.Call) and isinstance(node.func, ast.Name)]
        self.assertLess(next(n.lineno for n in calls if n.func.id == "admit"), next(n.lineno for n in calls if n.func.id == "execute"))

    def test_exact_variable_pts_override_and_restoration(self):
        class Processor:
            def _calculate_timestamps(self, indices, fps, merge_size=2):
                return [i / fps for i in indices]
        processor = Processor()
        original = processor._calculate_timestamps
        ids, pts = [10, 42, 88, 102], [5.01, 5.08, 6.4, 7.1]
        with exact_source_pts(processor, ids, pts, 5.0, 30.0) as record:
            times = processor._calculate_timestamps(ids, 30.0, 2)
            self.assertAlmostEqual(times[0], 0.045)
            self.assertAlmostEqual(times[1], 1.75)
            self.assertNotEqual(times, [10 / 30, 88 / 30])
        self.assertEqual(processor._calculate_timestamps, original)
        self.assertEqual(record["timestamp_clock"], "EXACT_SOURCE_PTS_OVERRIDE")
        self.assertEqual(len(record["processor_calls"]), 1)

    def test_processor_frame_identity_and_unexpanded_video_fail_closed(self):
        class Processor:
            def _calculate_timestamps(self, indices, fps, merge_size=2):
                return []
        processor = Processor()
        original = processor._calculate_timestamps
        with self.assertRaises(ValueError):
            with exact_source_pts(processor, [0, 5], [0.0, 0.8], 0, 30.0):
                processor._calculate_timestamps([0, 1], 30.0, 2)
        self.assertEqual(processor._calculate_timestamps, original)
        with self.assertRaises(ValueError):
            with exact_source_pts(processor, [0, 5], [0.0, 0.8], 0, 30.0):
                pass
        self.assertEqual(processor._calculate_timestamps, original)


if __name__ == "__main__":
    result = unittest.TextTestRunner(verbosity=2).run(unittest.defaultTestLoader.loadTestsFromTestCase(FormalCpuTests))
    report = {"status": "PASS_FORMAL_PREPARATION_CPU_ONLY" if result.wasSuccessful() else "FAIL_FORMAL_PREPARATION_CPU_ONLY",
              "tests_run": result.testsRun, "failures": len(result.failures), "errors": len(result.errors),
              "scope": "STOP refusal/stdlib admission/AST/exact PTS toy processor; no model, GPU, media decoder or optimizer"}
    (ROOT / "formal_cpu_test_report.json").write_text(json.dumps(report, indent=2) + "\n", encoding="utf-8")
    raise SystemExit(0 if result.wasSuccessful() else 1)
