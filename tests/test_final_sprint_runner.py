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


if __name__ == "__main__":
    unittest.main()
