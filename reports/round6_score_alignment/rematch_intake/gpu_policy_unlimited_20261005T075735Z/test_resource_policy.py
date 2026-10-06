"""CPU-only regression checks: importing the runner never calls main()."""
import importlib.util
import json
from pathlib import Path
import sys
import tempfile
import unittest

target = Path(sys.argv.pop(1)).resolve()
spec = importlib.util.spec_from_file_location("budget_policy_under_test", target)
runner = importlib.util.module_from_spec(spec)
spec.loader.exec_module(runner)


class PolicyTests(unittest.TestCase):
    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory(dir=Path(__file__).parent)
        self.path = Path(self.tmp.name) / "policy.json"

    def tearDown(self):
        self.tmp.cleanup()

    def load(self, mode, cap, **extra):
        self.path.write_text(json.dumps(dict(schema_version=1, gpu_time_mode=mode,
                                            max_total_gpu_seconds=cap, **extra)))
        return runner.load_resource_policy(self.path)

    def test_explicit_unlimited_allows_more_than_old_24_hours(self):
        runner.check_gpu_reservation(30 * 3600, 10 * 3600, 120,
                                     self.load("UNLIMITED", None))

    def test_finite_limit_still_rejects_overrun(self):
        with self.assertRaises(RuntimeError):
            runner.check_gpu_reservation(86300, 100, 120,
                                         self.load("FINITE", 86400))

    def test_finite_exact_limit_is_allowed(self):
        runner.check_gpu_reservation(86000, 280, 120, self.load("FINITE", 86400))

    def test_missing_policy_keeps_legacy_limit(self):
        policy = runner.load_resource_policy(self.path)
        self.assertEqual(policy["max_total_gpu_seconds"], 86400)
        with self.assertRaises(RuntimeError):
            runner.check_gpu_reservation(30 * 3600, 100, 120, policy)

    def test_inconsistent_unlimited_rejected(self):
        with self.assertRaises(ValueError):
            self.load("UNLIMITED", 86400)

    def test_bad_finite_limits_rejected(self):
        for cap in (None, True, 0, -1, 86400.0, float("nan"), float("inf")):
            with self.subTest(cap=cap), self.assertRaises(ValueError):
                self.load("FINITE", cap)

    def test_unknown_mode_and_missing_limit_rejected(self):
        with self.assertRaises(ValueError):
            self.load("UNKNOWN", None)
        self.path.write_text('{"schema_version":1,"gpu_time_mode":"UNLIMITED"}')
        with self.assertRaises(ValueError):
            runner.load_resource_policy(self.path)

    def test_single_job_limit_still_required(self):
        for limit in (0, -1, True, None):
            with self.subTest(limit=limit), self.assertRaises(ValueError):
                runner.check_gpu_reservation(0, limit, 120, self.load("UNLIMITED", None))

    def test_loaded_policy_records_exact_digest(self):
        import hashlib
        policy = self.load("UNLIMITED", None)
        self.assertEqual(policy["policy_sha256"],
                         hashlib.sha256(self.path.read_bytes()).hexdigest())


if __name__ == "__main__":
    unittest.main(verbosity=2)
