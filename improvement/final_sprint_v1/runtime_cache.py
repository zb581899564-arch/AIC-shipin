"""Durable exact-call journal shared by physical phase and grounding inference.

An atomic returned-result envelope is itself recoverable evidence: a crash
between that write and the success marker never repeats a successful call.
Incomplete claims and explicit failures require owned-wrapper reconciliation.
No timeouts, stale PIDs, nearest assets, default answers or latest directories
are interpreted as authority to rerun or substitute work.
"""
from __future__ import annotations

from pathlib import Path
import time

from .contracts import atomic_new, checked, ref, require, stable_key, strict_load, utc_now
from .state import TaskClaim, TaskStore, UnresolvedClaim


class CallJournal:
    def __init__(self, root, base_binding, budget=None):
        require(isinstance(base_binding, dict) and base_binding, "Exact code/config/model base binding required")
        self.store = TaskStore(root)
        self.base_binding = dict(base_binding)
        self.budget = budget

    def _binding(self, call_binding):
        require(isinstance(call_binding, dict) and call_binding, "Exact physical call binding required")
        return {"base": self.base_binding, "call": call_binding,
                "journal_schema": "AIC_FINAL_CALL_V1"}

    @staticmethod
    def _packet(path, task_id, binding_sha):
        packet = strict_load(path)
        require(packet.get("schema") == "AIC_FINAL_CALL_V1"
                and packet.get("binding_sha256") == binding_sha
                and packet.get("task_id") == task_id
                and packet.get("status") == "FUNCTION_RETURNED_COMPLETE"
                and isinstance(packet.get("result"), dict)
                and isinstance(packet.get("accounting"), dict),
                "Atomic returned model result has a different or incomplete identity")
        return packet

    def _existing(self, task_id, call_binding):
        binding = self._binding(call_binding)
        task = self.store._task(task_id)
        pointer = task / "state.json"
        if not pointer.exists():
            return None
        state = strict_load(pointer)
        binding_sha = stable_key(binding)
        require(state["binding_sha256"] == binding_sha, "Call ID already has different exact assets/code/config")
        directory = task / "attempts" / str(state["active_attempt"])
        claim_value = strict_load(directory / "claim.json")
        require(claim_value["binding_sha256"] == binding_sha and claim_value["binding"] == binding,
                "Call claim binding differs")
        raw = directory / "returned_result.json"
        if (directory / "success.json").exists():
            claim = self.store.claim(task_id, binding)
            require(claim.reused, "Existing durable call was not adopted")
            identity = claim.result["artifacts"]["result"]
            packet = self._packet(checked(identity), task_id, binding_sha)
            return packet, identity
        if raw.exists() and not (directory / "failure.json").exists():
            packet = self._packet(raw, task_id, binding_sha)
            identity = ref(raw)
            claim = TaskClaim(self.store, task_id, directory, binding_sha)
            claim.complete({"result": identity}, payload={"accounting": packet["accounting"]})
            return packet, identity
        if raw.exists():
            raise UnresolvedClaim("Durable returned output coexists with a later failure; adopt/reconcile it, never rerun: " + task_id)
        if state.get("status") == "RESOLVED_RETRY_ALLOWED":
            return None
        raise UnresolvedClaim("Call has no durable successful result; inspect exact owned-wrapper terminal: " + task_id)

    def has(self, task_id, call_binding):
        return self._existing(task_id, call_binding) is not None

    def get(self, task_id, call_binding):
        result = self._existing(task_id, call_binding)
        return None if result is None else result[0]["result"]

    def result_ref(self, task_id, call_binding):
        result = self._existing(task_id, call_binding)
        require(result is not None, "Requested call has no successful durable result")
        return result[1]

    def reconcile(self, task_id, wrapper_terminal_ref):
        """Resolve only the exact active owned attempt, without calling a model.

        A completed function result survives even a later logging/terminal
        failure.  Its adoption records a new success artifact and preserves
        the original failure, rather than pretending that the failure never
        occurred.  Without a durable result, the wrapper proof may authorize
        the next explicit call; elapsed time and PID state never authorize it.
        """
        task = self.store._task(task_id)
        pointer = strict_load(task / "state.json")
        directory = task / "attempts" / str(pointer["active_attempt"])
        claim_path = directory / "claim.json"
        claim = strict_load(claim_path)
        binding = claim.get("binding")
        require(isinstance(binding, dict) and binding.get("base") == self.base_binding
                and binding.get("journal_schema") == "AIC_FINAL_CALL_V1"
                and claim.get("task_id") == task_id,
                "Recovery claim differs from current exact code/config/model base")
        call_binding = binding.get("call")
        require(binding == self._binding(call_binding), "Recovery call binding has unexpected fields")
        binding_sha = stable_key(binding)
        require(pointer.get("binding_sha256") == binding_sha
                and claim.get("binding_sha256") == binding_sha, "Recovery claim hash differs")
        try:
            existing = self._existing(task_id, call_binding)
        except UnresolvedClaim:
            existing = None
        if existing is not None:
            return {"status": "SUCCESS", "recovery_action": "ADOPTED_EXISTING_SUCCESS",
                    "task_id": task_id, "result_ref": existing[1], "model_calls": 0}

        proof = strict_load(checked(wrapper_terminal_ref))
        require(proof.get("task_id") == task_id and proof.get("work_terminated") is True
                and proof.get("no_external_task_signaled") is True
                and proof.get("claim_sha256") == ref(claim_path)["sha256"]
                and proof.get("termination_basis") == "owned_wrapper_terminal",
                "Explicit owned-wrapper terminal proof required; PID/timeout is insufficient")
        raw = directory / "returned_result.json"
        if raw.exists():
            packet = self._packet(raw, task_id, binding_sha)
            failure_path = directory / "failure.json"
            require(failure_path.exists(), "Unexpected unfinished adoption state; inspect exact attempt")
            identity = ref(raw)
            adopted = {"status": "SUCCESS", "task_id": task_id,
                "binding_sha256": binding_sha, "artifacts": {"result": identity},
                "completed_at": packet.get("completed_at", claim["claimed_at"]),
                "payload": {"accounting": packet["accounting"], "recovery": {
                    "returned_result_adopted_without_model_call": True,
                    "original_failure": ref(failure_path),
                    "wrapper_terminal": wrapper_terminal_ref,
                    "accounting_note": "Returned result and later failure overlap one original attempt; recovery ran no inference."}}}
            adoption_path = directory / "adopted_returned_success.json"
            if adoption_path.exists():
                require(strict_load(adoption_path) == adopted,
                        "Existing returned-result adoption has a different exact identity")
                adoption_ref = ref(adoption_path)
            else:
                adoption_ref = atomic_new(adoption_path, adopted)
            self.store.resolve_interrupted(task_id, binding, wrapper_terminal_ref,
                                           durable_success=adoption_ref)
            existing = self._existing(task_id, call_binding)
            require(existing is not None, "Reconciled returned result was not adopted")
            return {"status": "SUCCESS", "recovery_action": "ADOPTED_RETURNED_RESULT_AFTER_FAILURE",
                    "task_id": task_id, "result_ref": existing[1],
                    "adoption_ref": adoption_ref, "original_failure": ref(failure_path), "model_calls": 0}
        resolution = self.store.resolve_interrupted(task_id, binding, wrapper_terminal_ref)
        return {"status": "RESOLVED_RETRY_ALLOWED", "task_id": task_id,
                "recovery_action": "OWNED_TERMINATED_ATTEMPT_WITHOUT_RESULT",
                "resolution": resolution, "model_calls": 0}

    def call(self, task_id, call_binding, fn):
        existing = self._existing(task_id, call_binding)
        if existing is not None:
            return existing[0]["result"]
        if self.budget is not None:
            self.budget.check()
        claim = self.store.claim(task_id, self._binding(call_binding))
        if claim.reused:
            return strict_load(checked(claim.result["artifacts"]["result"]))["result"]
        started = time.monotonic()
        try:
            result = fn()
            require(isinstance(result, dict), "A complete serializable inference/source-result object is required")
            elapsed = time.monotonic() - started
            physical = result.get("physical_model_forwards", 0)
            require(type(physical) is int and physical >= 0, "Invalid actual physical-forward count")
            accounting = {"wall_seconds": elapsed, "includes_current_call_failure": False,
                          "physical_model_forwards": physical, "function_calls": 1,
                          "actual_gpu_kernel_seconds": "NOT_INDEPENDENTLY_METERED"}
            packet = {"schema": "AIC_FINAL_CALL_V1", "status": "FUNCTION_RETURNED_COMPLETE",
                      "binding_sha256": claim.binding_sha, "task_id": task_id,
                      "completed_at": utc_now(), "result": result, "accounting": accounting}
            identity = atomic_new(claim.directory / "returned_result.json", packet)
            claim.complete({"result": identity}, payload={"accounting": accounting})
            if self.budget is not None:
                self.budget.calls += physical
            return result
        except BaseException as error:
            claim.fail(error, accounting={"wall_seconds": time.monotonic() - started,
                                          "includes_current_call_failure": True, "function_calls": 1,
                                          "physical_model_forwards": "UNKNOWN_IF_FUNCTION_FAILED",
                                          "failure_is_not_empty": True})
            raise
