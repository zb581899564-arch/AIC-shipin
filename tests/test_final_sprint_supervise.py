"""Failure-injection checks for owned-child cleanup; no real GPU task launched."""
from contextlib import redirect_stdout
from datetime import datetime, timedelta, timezone
import io
import json
from pathlib import Path
import signal
import tempfile
import unittest
from unittest.mock import Mock, patch

from improvement.final_sprint_v1 import supervise


class OwnedWrapperContracts(unittest.TestCase):
    def fixtures(self, directory):
        root = Path(directory)
        assets_path = root / "assets.json"
        assets_path.write_text('{"synthetic_test_only":true}')
        value = {"run_root": str(root), "deadline": (datetime.now(timezone.utc) + timedelta(hours=8)).isoformat(),
                 "resources": {"finalization_reserve_seconds": 4 * 3600}}
        argv = ["--assets", str(assets_path), "--expected-commit", "a" * 40,
                "--candidate", "g_subject", "--action", "run"]
        cost = {"total_execution_seconds": 64800, "confirmed_command_wall_seconds": 100,
                "unresolved_reserved_seconds": 0}
        return root, value, argv, cost

    def test_wrapper_sigterm_cleans_only_its_actual_owned_group_then_writes_terminal(self):
        with tempfile.TemporaryDirectory() as directory:
            root, value, argv, cost = self.fixtures(directory)
            child = Mock(pid=123456, returncode=-15)
            child.wait.side_effect = [supervise.OwnedWrapperStop("SIGTERM"), -15]
            child.poll.return_value = None
            with patch.object(supervise, "load", return_value=value), \
                 patch("improvement.final_sprint_v1.resources.cumulative_execution", return_value=cost), \
                 patch.object(supervise.subprocess, "Popen", return_value=child), \
                 patch.object(supervise.os, "killpg") as kill, \
                 patch.object(supervise.signal, "signal"), redirect_stdout(io.StringIO()):
                self.assertEqual(supervise.main(argv), 1)
            kill.assert_called_once_with(child.pid, signal.SIGTERM)
            self.assertEqual(child.wait.call_count, 2)
            terminals = list((root / "wrappers").glob("*/completion.json"))
            self.assertEqual(len(terminals), 1)
            terminal = json.loads(terminals[0].read_text())
            self.assertTrue(terminal["work_terminated"])
            self.assertTrue(terminal["no_external_task_signaled"])

    def test_exhausted_total_budget_cannot_launch_a_child(self):
        with tempfile.TemporaryDirectory() as directory:
            _, value, argv, cost = self.fixtures(directory)
            cost["confirmed_command_wall_seconds"] = cost["total_execution_seconds"]
            with patch.object(supervise, "load", return_value=value), \
                 patch("improvement.final_sprint_v1.resources.cumulative_execution", return_value=cost), \
                 patch.object(supervise.subprocess, "Popen") as launch:
                with self.assertRaisesRegex(ValueError, "Cumulative command budget"):
                    supervise.main(argv)
                launch.assert_not_called()


if __name__ == "__main__":
    unittest.main()
