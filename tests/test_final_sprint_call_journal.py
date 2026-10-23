"""Durable-call recovery tests; no model execution or quality assertions."""
from pathlib import Path
import os
import tempfile
import unittest
from unittest.mock import patch

from improvement.final_sprint_v1.contracts import atomic_new, checked, ref, stable_key, strict_load
from improvement.final_sprint_v1.runtime_cache import CallJournal
from improvement.final_sprint_v1.state import UnresolvedClaim


class CallJournalContracts(unittest.TestCase):
    def setUp(self):
        self.temporary = tempfile.TemporaryDirectory()
        self.root = Path(self.temporary.name)
        self.journal = CallJournal(self.root, {"code": "exact-code", "model": "exact-model"})
        self.binding = {"source_sha256": "a" * 64, "clip": "clip_00000", "phase_policy": "fixed"}

    def tearDown(self):
        self.temporary.cleanup()

    def test_successful_call_is_adopted_without_invoking_model_again(self):
        calls = []
        def model():
            calls.append(True)
            return {"status": "LEGAL_EMPTY", "physical_model_forwards": 17, "frames": []}
        first = self.journal.call("phase_source_clip", self.binding, model)
        second = self.journal.call("phase_source_clip", self.binding, model)
        self.assertEqual(first, second)
        self.assertEqual(calls, [True])
        self.assertTrue(self.journal.has("phase_source_clip", self.binding))
        self.assertEqual(strict_load(checked(self.journal.result_ref("phase_source_clip", self.binding)))["result"], first)

    def test_atomic_function_return_survives_crash_before_success_marker(self):
        binding = self.journal._binding(self.binding)
        claim = self.journal.store.claim("phase_source_clip", binding)
        value = {"schema": "AIC_FINAL_CALL_V1", "status": "FUNCTION_RETURNED_COMPLETE",
                 "binding_sha256": stable_key(binding), "task_id": "phase_source_clip",
                 "result": {"phase": "ordinary"},
                 "accounting": {"wall_seconds": 2.1}}
        atomic_new(claim.directory / "returned_result.json", value)
        actual = self.journal.call("phase_source_clip", self.binding, lambda: self.fail("Model rerun"))
        self.assertEqual(actual, value["result"])
        self.assertTrue((claim.directory / "success.json").exists())
        self.assertTrue((claim.directory / "completion.json").exists())

    def test_failed_call_is_not_retried_or_returned_as_empty(self):
        def fails():
            raise RuntimeError("CUDA input failure")
        with self.assertRaisesRegex(RuntimeError, "CUDA input"):
            self.journal.call("phase_source_clip", self.binding, fails)
        with self.assertRaises(UnresolvedClaim):
            self.journal.call("phase_source_clip", self.binding, lambda: self.fail("Automatic retry"))
        failure = strict_load(self.root / "tasks/phase_source_clip/attempts/1/failure.json")
        self.assertTrue(failure["accounting"]["includes_current_call_failure"])
        self.assertGreaterEqual(failure["accounting"]["wall_seconds"], 0)

    def test_foreign_binding_cannot_reuse_success(self):
        self.journal.call("phase_source_clip", self.binding, lambda: {"frames": []})
        with self.assertRaisesRegex(ValueError, "different exact"):
            self.journal.get("phase_source_clip", dict(self.binding, source_sha256="b" * 64))

    def test_incomplete_live_claim_is_not_timeout_restart_authority(self):
        self.journal.store.claim("phase_source_clip", self.journal._binding(self.binding))
        with self.assertRaises(UnresolvedClaim):
            self.journal.has("phase_source_clip", self.binding)

    def _interrupted(self, *, returned):
        task_id = "phase_source_clip"
        binding = self.journal._binding(self.binding)
        claim = self.journal.store.claim(task_id, binding)
        if returned:
            atomic_new(claim.directory / "returned_result.json", {
                "schema": "AIC_FINAL_CALL_V1", "status": "FUNCTION_RETURNED_COMPLETE",
                "binding_sha256": stable_key(binding), "task_id": task_id,
                "completed_at": "2026-10-23T00:00:00+00:00",
                "result": {"phases": ["ordinary"], "physical_model_forwards": 17},
                "accounting": {"wall_seconds": 2.1, "physical_model_forwards": 17}})
        claim.fail(RuntimeError("Simulated wrapper failure after possible durable result"),
                   accounting={"wall_seconds": 2.2})
        proof = {"task_id": task_id, "claim_sha256": ref(claim.directory / "claim.json")["sha256"],
                 "work_terminated": True, "termination_basis": "owned_wrapper_terminal",
                 "no_external_task_signaled": True}
        return claim, proof

    def test_returned_result_with_later_failure_is_explicitly_adopted_without_rerun(self):
        claim, proof = self._interrupted(returned=True)
        original_failure = ref(claim.directory / "failure.json")
        evidence = atomic_new(self.root / "owned_terminal.json", proof)
        actual = self.journal.reconcile("phase_source_clip", evidence)
        self.assertEqual(actual["recovery_action"], "ADOPTED_RETURNED_RESULT_AFTER_FAILURE")
        self.assertEqual(actual["model_calls"], 0)
        self.assertEqual(ref(claim.directory / "failure.json"), original_failure)
        self.assertTrue((claim.directory / "adopted_returned_success.json").exists())
        result = self.journal.call("phase_source_clip", self.binding, lambda: self.fail("Successful GPU call repeated"))
        self.assertEqual(result["physical_model_forwards"], 17)
        again = self.journal.reconcile("phase_source_clip", None)
        self.assertEqual(again["recovery_action"], "ADOPTED_EXISTING_SUCCESS")

    def test_missing_result_needs_exact_terminal_then_explicit_retry(self):
        claim, proof = self._interrupted(returned=False)
        evidence = atomic_new(self.root / "owned_terminal.json", proof)
        actual = self.journal.reconcile("phase_source_clip", evidence)
        self.assertEqual(actual["status"], "RESOLVED_RETRY_ALLOWED")
        calls = []
        result = self.journal.call("phase_source_clip", self.binding,
                                  lambda: calls.append(True) or {"frames": []})
        self.assertEqual(result, {"frames": []})
        self.assertEqual(calls, [True])
        self.assertTrue((claim.directory / "failure.json").exists())
        self.assertTrue((self.root / "tasks/phase_source_clip/attempts/2/success.json").exists())

    def test_wrong_claim_or_foreign_base_cannot_adopt_or_authorize_retry(self):
        claim, proof = self._interrupted(returned=True)
        proof["claim_sha256"] = "f" * 64
        evidence = atomic_new(self.root / "wrong_terminal.json", proof)
        with self.assertRaisesRegex(ValueError, "owned-wrapper terminal"):
            self.journal.reconcile("phase_source_clip", evidence)
        other = CallJournal(self.root, {"code": "other-code", "model": "exact-model"})
        with self.assertRaisesRegex(ValueError, "current exact"):
            other.reconcile("phase_source_clip", evidence)
        self.assertFalse((claim.directory / "adopted_returned_success.json").exists())
        self.assertFalse((claim.directory / "resolution.json").exists())

    def test_orphan_initial_pointer_requires_exact_terminal_then_preserves_result(self):
        claim, proof = self._interrupted(returned=True)
        pointer = self.root / "tasks/phase_source_clip/state.json"
        pointer.unlink()  # Inject claim-before-state crash window.
        proof["claim_ref"] = ref(claim.directory / "claim.json")
        evidence = atomic_new(self.root / "orphan_terminal.json", proof)
        with self.assertRaisesRegex(UnresolvedClaim, "without its state pointer"):
            self.journal.call("phase_source_clip", self.binding, lambda: self.fail("Orphan rerun"))
        recovered = self.journal.reconcile("phase_source_clip", evidence)
        self.assertEqual(recovered["model_calls"], 0)
        self.assertEqual(recovered["recovery_action"], "ADOPTED_RETURNED_RESULT_AFTER_FAILURE")
        actual = self.journal.call("phase_source_clip", self.binding, lambda: self.fail("Successful result repeated"))
        self.assertEqual(actual["physical_model_forwards"], 17)
        self.assertEqual(len(list((self.root / "tasks/phase_source_clip/attempts").iterdir())), 1)

    def test_orphan_without_return_requires_terminated_claim_before_retry(self):
        claim, proof = self._interrupted(returned=False)
        (self.root / "tasks/phase_source_clip/state.json").unlink()
        proof["claim_ref"] = ref(claim.directory / "claim.json")
        evidence = atomic_new(self.root / "orphan_terminal.json", proof)
        self.assertEqual(self.journal.reconcile("phase_source_clip", evidence)["status"], "RESOLVED_RETRY_ALLOWED")
        calls = []
        self.journal.call("phase_source_clip", self.binding, lambda: calls.append(True) or {"frames": []})
        self.assertEqual(calls, [True])
        self.assertTrue((self.root / "tasks/phase_source_clip/attempts/2/success.json").exists())

    def test_correct_claim_hash_but_wrong_wrapper_does_not_authorize_retry(self):
        with patch.dict(os.environ, {"AIC_FINAL_WRAPPER_ID": "a" * 32}):
            claim, proof = self._interrupted(returned=False)
        proof["owned_wrapper_id"] = "b" * 32
        evidence = atomic_new(self.root / "wrong_wrapper.json", proof)
        with self.assertRaisesRegex(ValueError, "different owned wrapper"):
            self.journal.reconcile("phase_source_clip", evidence)
        self.assertFalse((claim.directory / "resolution.json").exists())


if __name__ == "__main__":
    unittest.main()
