"""Durable per-task claims, successes and accounting; no PID-based auto-retry.

A durable success is written before its terminal marker. Recovery adopts that
success even if the process died between the writes. Interrupted claims require
an explicit wrapper-terminal resolution, never a timeout or stale PID guess.
"""
from __future__ import annotations

from contextlib import contextmanager
import fcntl
import os
from pathlib import Path
import re
import socket
import uuid

from .contracts import atomic_new, canonical_bytes, checked, ref, require, strict_load, stable_key, utc_now


class UnresolvedClaim(RuntimeError):
    """An existing task needs terminal reconciliation before execution can resume."""


@contextmanager
def _locked(path):
    with Path(path).open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _replace_pointer(path, value):
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex)
    atomic_new(temporary, value)
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _validated_success(path, binding_sha):
    result = strict_load(path)
    require(result.get("status") == "SUCCESS" and result.get("binding_sha256") == binding_sha,
            "Successful task has a different exact execution binding")
    require(isinstance(result.get("artifacts"), dict) and result["artifacts"],
            "Successful task must identify durable output artifacts")
    for identity in result["artifacts"].values():
        checked(identity)
    return result


class TaskClaim:
    def __init__(self, store, task_id, directory, binding_sha, reused=False, result=None):
        self.store, self.task_id, self.directory = store, task_id, directory
        self.binding_sha, self.reused, self.result = binding_sha, reused, result

    def __enter__(self):
        return self

    def __exit__(self, kind, error, traceback):
        if error is not None and not self.reused:
            self.fail(error)
        return False

    def complete(self, artifacts, payload=None):
        if self.reused:
            return self.result
        require(isinstance(artifacts, dict) and artifacts, "Durable task outputs must be explicit")
        for identity in artifacts.values():
            checked(identity)
        result = {"status": "SUCCESS", "task_id": self.task_id,
                  "binding_sha256": self.binding_sha, "artifacts": artifacts,
                  "payload": payload or {}, "completed_at": utc_now()}
        with _locked(self.directory.parent.parent / "task.lock"):
            require(not (self.directory / "failure.json").exists(), "Failed task cannot become successful")
            if (self.directory / "success.json").exists():
                old = _validated_success(self.directory / "success.json", self.binding_sha)
                require(old["artifacts"] == artifacts and old["payload"] == (payload or {}),
                        "Refusing to overwrite a different durable success")
                result = old
            else:
                atomic_new(self.directory / "success.json", result)
            if not (self.directory / "completion.json").exists():
                atomic_new(self.directory / "completion.json", {
                    "status": "SUCCESS", "success": ref(self.directory / "success.json"),
                    "binding_sha256": self.binding_sha, "terminal_at": utc_now()})
        self.result = result
        self.store._event("SUCCESS", self.task_id, self.directory, self.binding_sha,
                          artifact_refs=artifacts, accounting=(payload or {}).get("accounting", {}))
        return result

    def fail(self, error, *, accounting=None):
        if self.reused or (self.directory / "success.json").exists():
            return  # A later logging/error path must never revoke durable success.
        with _locked(self.directory.parent.parent / "task.lock"):
            if not (self.directory / "failure.json").exists():
                atomic_new(self.directory / "failure.json", {
                    "status": "FAILED", "task_id": self.task_id,
                    "binding_sha256": self.binding_sha, "failed_at": utc_now(),
                    "error_type": type(error).__name__, "error": str(error),
                    "accounting": accounting or {}, "failure_is_not_empty": True})
                self.store._event("FAILED", self.task_id, self.directory, self.binding_sha,
                                  accounting=accounting or {})


class TaskStore:
    def __init__(self, root):
        self.root = Path(root).resolve()
        self.root.mkdir(parents=True, exist_ok=True)
        (self.root / "tasks").mkdir(exist_ok=True)
        self._ledger_offset = 0
        self._event_ids = set()

    def _task(self, task_id):
        require(isinstance(task_id, str) and re.fullmatch(r"[A-Za-z0-9_.-]{1,160}", task_id)
                and task_id not in {".", ".."}, "Safe stable task ID required")
        return self.root / "tasks" / task_id

    def _event(self, event, task_id, directory, binding_sha, **extra):
        event_id = stable_key(event, task_id, str(directory.relative_to(self.root)), binding_sha)
        value = {"event": event, "event_id": event_id, "task_id": task_id,
                 "attempt": str(directory.relative_to(self.root)),
                 "binding_sha256": binding_sha, "time": utc_now(), **extra}
        with _locked(self.root / "ledger.lock"):
            ledger = self.root / "ledger.jsonl"
            if ledger.exists():
                require(ledger.stat().st_size >= self._ledger_offset, "Accounting ledger was truncated externally")
                with ledger.open("rb") as stream:
                    stream.seek(self._ledger_offset)
                    tail = stream.read()
                require(not tail or tail.endswith(b"\n"),
                        "Partial accounting ledger record requires reconciliation; never rerun successful work")
                from .contracts import strict_loads
                for line in tail.splitlines():
                    record = strict_loads(line)
                    self._event_ids.add(record["event_id"])
                self._ledger_offset += len(tail)
            if event_id in self._event_ids:
                return
            data = canonical_bytes(value) + b"\n"
            with ledger.open("ab") as stream:
                stream.write(data)
                stream.flush()
                os.fsync(stream.fileno())
            self._event_ids.add(event_id)
            self._ledger_offset += len(data)

    def claim(self, task_id, binding):
        require(isinstance(binding, dict) and binding, "Exact nonempty task binding required")
        task = self._task(task_id)
        task.mkdir(exist_ok=True)
        binding_sha = stable_key(binding)
        with _locked(task / "task.lock"):
            pointer_path = task / "state.json"
            if pointer_path.exists():
                pointer = strict_load(pointer_path)
                require(pointer.get("binding_sha256") == binding_sha,
                        "Task ID already belongs to different assets/code/config")
                directory = task / "attempts" / str(pointer["active_attempt"])
                claim = strict_load(directory / "claim.json")
                require(claim["binding_sha256"] == binding_sha, "Claim identity differs")
                success = directory / "success.json"
                if success.exists():
                    result = _validated_success(success, binding_sha)
                    terminal = directory / "completion.json"
                    if terminal.exists():
                        complete = strict_load(terminal)
                        require(complete.get("status") == "SUCCESS" and
                                complete.get("binding_sha256") == binding_sha,
                                "Existing terminal differs from durable success")
                        require(checked(complete["success"]) == success.resolve(),
                                "Terminal refers to a different successful task")
                    else:
                        atomic_new(terminal, {"status": "SUCCESS", "success": ref(success),
                                             "binding_sha256": binding_sha, "terminal_at": utc_now(),
                                             "reconciled_durable_success": True})
                    self._event("SUCCESS", task_id, directory, binding_sha,
                                artifact_refs=result["artifacts"],
                                accounting=result["payload"].get("accounting", {}))
                    return TaskClaim(self, task_id, directory, binding_sha, True, result)
                if (directory / "completion.json").exists():
                    raise UnresolvedClaim("Terminal exists without its durable success: " + task_id)
                if pointer.get("status") != "RESOLVED_RETRY_ALLOWED":
                    raise UnresolvedClaim("Existing claim is not a completed success; reconcile exact wrapper terminal: " + task_id)
                resolution = strict_load(checked(pointer["resolution"]))
                require(resolution.get("retry_allowed") is True and
                        resolution.get("binding_sha256") == binding_sha,
                        "Explicit terminated-attempt resolution missing")
                attempt = pointer["active_attempt"] + 1
            else:
                attempt = 1
            directory = task / "attempts" / str(attempt)
            directory.mkdir(parents=True, exist_ok=False)
            atomic_new(directory / "claim.json", {"task_id": task_id, "attempt": attempt,
                "claim_id": uuid.uuid4().hex, "binding": binding, "binding_sha256": binding_sha,
                "host": socket.gethostname(), "pid": os.getpid(), "claimed_at": utc_now(),
                "owned_wrapper_id": os.environ.get("AIC_FINAL_WRAPPER_ID"),
                "pid_is_not_restart_authority": True})
            _replace_pointer(pointer_path, {"binding_sha256": binding_sha,
                "active_attempt": attempt, "status": "CLAIMED"})
        self._event("CLAIMED", task_id, directory, binding_sha)
        return TaskClaim(self, task_id, directory, binding_sha)

    def resolve_interrupted(self, task_id, binding, evidence, *, durable_success=None):
        """Called only after inspecting the exact scheduler/wrapper terminal.

        Evidence JSON must bind ``claim_sha256``, ``task_id``, declare
        ``work_terminated: true`` and ``no_external_task_signaled: true``. It is
        produced from the owned task's terminal, not from a stale PID/timeout.
        A valid durable success is adopted before any retry is considered.
        """
        task, binding_sha = self._task(task_id), stable_key(binding)
        with _locked(task / "task.lock"):
            pointer = strict_load(task / "state.json")
            require(pointer["binding_sha256"] == binding_sha, "Recovery binding differs")
            directory = task / "attempts" / str(pointer["active_attempt"])
            existing = directory / "success.json"
            if existing.exists():
                return _validated_success(existing, binding_sha)
            proof = strict_load(checked(evidence))
            require(proof.get("task_id") == task_id and proof.get("work_terminated") is True and
                    proof.get("no_external_task_signaled") is True and
                    proof.get("claim_sha256") == ref(directory / "claim.json")["sha256"] and
                    proof.get("termination_basis") == "owned_wrapper_terminal",
                    "Explicit owned-wrapper terminal proof required; PID/timeout is insufficient")
            if durable_success is not None:
                adopted = _validated_success(checked(durable_success), binding_sha)
                require(adopted["task_id"] == task_id, "Durable success belongs to a different task")
                atomic_new(existing, adopted)
                atomic_new(directory / "completion.json", {"status": "SUCCESS", "success": ref(existing),
                    "binding_sha256": binding_sha, "terminal_at": utc_now(), "adopted_success": durable_success})
                return adopted
            resolution = {"task_id": task_id, "binding_sha256": binding_sha, "evidence": evidence,
                          "retry_allowed": True, "resolved_at": utc_now(), "no_durable_success_found": True}
            resolution_path = directory / "resolution.json"
            if resolution_path.exists():
                old = strict_load(resolution_path)
                require(old["evidence"] == evidence and old["binding_sha256"] == binding_sha,
                        "Recovery already has a different resolution")
            else:
                atomic_new(resolution_path, resolution)
            _replace_pointer(task / "state.json", {"binding_sha256": binding_sha,
                "active_attempt": pointer["active_attempt"], "status": "RESOLVED_RETRY_ALLOWED",
                "resolution": ref(resolution_path)})
        self._event("TERMINATED_ATTEMPT_RESOLVED", task_id, directory, binding_sha, evidence=evidence)
        return resolution
