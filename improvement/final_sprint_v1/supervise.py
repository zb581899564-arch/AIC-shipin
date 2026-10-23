"""Own one finite child command and write exact terminal proofs after wait().

This wrapper may stop only its newly created child process group. It never
signals a pre-existing PID, Java process, scheduler or external GPU task.
Completed calls remain immutable. Reconciliation is a separate explicit CLI.
"""
from __future__ import annotations

import argparse
from datetime import datetime, timezone
import os
from pathlib import Path
import signal
import socket
import subprocess
import sys
import time
import uuid

from .assets import candidate_registry, load
from .contracts import atomic_new, ref, require, strict_load, utc_now


class OwnedWrapperStop(BaseException):
    pass


def terminal_claims(root, wrapper_id, child_pid, elapsed, destination):
    commands, tasks = [], []
    for kind, paths in (
        ("task", (root / "journal" / "tasks").glob("*/attempts/*/claim.json")),
        ("command", (root / "command_budget").glob("*/claim.json")),
    ):
        for path in paths:
            claim = strict_load(path)
            if claim.get("owned_wrapper_id") != wrapper_id:
                continue
            require(claim.get("host") == socket.gethostname() and claim.get("pid") == child_pid,
                    "Wrapper may prove only its exact owned child claims")
            identity = claim["task_id"] if kind == "task" else claim["command_id"]
            proof = {"schema": "AIC_FINAL_TERMINATED_CLAIM_V1", kind + "_id": identity,
                     "claim_sha256": ref(path)["sha256"], "claim_ref": ref(path),
                     "owned_wrapper_id": wrapper_id, "work_terminated": True,
                     "termination_basis": "owned_wrapper_terminal", "no_external_task_signaled": True,
                     "wall_seconds_including_load_decode_failures": elapsed,
                     "wall_basis": "Entire owned subprocess lifetime; conservative if claim began later"}
            location = destination / (kind + "_" + identity + "_" + str(claim.get("attempt", 1)) + ".json")
            proof_ref = atomic_new(location, proof)
            (tasks if kind == "task" else commands).append({kind + "_id": identity, "terminal_ref": proof_ref})
    return tasks, commands


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--assets", required=True)
    parser.add_argument("--expected-commit", required=True)
    parser.add_argument("--candidate", required=True)
    parser.add_argument("--action", choices=("smoke", "run"), required=True)
    args = parser.parse_args(argv)
    assets = load(args.assets, expected_commit=args.expected_commit)
    registry = candidate_registry()["candidates"]
    require(args.candidate in registry, "Unknown preregistered candidate")
    root = Path(assets["run_root"])
    wrapper_id = uuid.uuid4().hex
    directory = root / "wrappers" / wrapper_id
    directory.mkdir(parents=True, exist_ok=False)
    claims_dir = directory / "terminated_claims"
    claims_dir.mkdir()
    command = [sys.executable, "-m", "improvement.final_sprint_v1.cli", args.action,
               "--assets", str(Path(args.assets).resolve()), "--expected-commit", args.expected_commit,
               "--candidate", args.candidate]
    cap = 1800 if args.action == "smoke" else registry[args.candidate]["stage_seconds_cap"]
    deadline = datetime.fromisoformat(assets["deadline"].replace("Z", "+00:00"))
    available = (deadline - datetime.now(timezone.utc)).total_seconds() - assets["resources"]["finalization_reserve_seconds"]
    from .resources import cumulative_execution
    used = cumulative_execution(assets)
    cumulative_left = used["total_execution_seconds"] - used["confirmed_command_wall_seconds"] - used["unresolved_reserved_seconds"]
    require(available > 60, "No production time remains before finalization reserve")
    require(cumulative_left > 0, "Cumulative command budget is spent or reserved by unresolved work")
    timeout = min(cap + 120, available, cumulative_left)
    started = time.monotonic()
    env = dict(os.environ, AIC_FINAL_WRAPPER_ID=wrapper_id,
               AIC_FINAL_COMMAND_STARTED_MONOTONIC=str(started))
    stopped, stop_reason = False, None
    previous_handlers = {sig: signal.getsignal(sig) for sig in (signal.SIGTERM, signal.SIGINT)}
    def interrupted(signum, _frame):
        raise OwnedWrapperStop("Received owned-wrapper signal " + str(signum))
    for sig in previous_handlers:
        signal.signal(sig, interrupted)
    child = None
    with (directory / "command.log").open("xb") as stream:
        try:
            child = subprocess.Popen(command, stdout=stream, stderr=subprocess.STDOUT,
                                     env=env, start_new_session=True)
            atomic_new(directory / "claim.json", {"wrapper_id": wrapper_id, "asset_lock": ref(args.assets),
                "command": command, "child_pid": child.pid, "owned_process_group": child.pid,
                "started_at": utc_now(), "timeout_seconds": timeout, "no_external_task_signaled": True})
            print("WRAPPER_STARTED " + str(directory), flush=True)
            code = child.wait(timeout=timeout)
        except BaseException as error:
            stopped, stop_reason = True, type(error).__name__
            if child is None:
                raise
        finally:
            # Ignore a second interrupt while waiting for our own children to
            # terminate. No unrelated process group is ever selected.
            for sig in previous_handlers:
                signal.signal(sig, signal.SIG_IGN)
            if child is not None and child.poll() is None:
                os.killpg(child.pid, signal.SIGTERM)
                try:
                    child.wait(timeout=60)
                except subprocess.TimeoutExpired:
                    os.killpg(child.pid, signal.SIGKILL)
                    child.wait()
            if child is not None:
                code = child.returncode
            for sig, handler in previous_handlers.items():
                signal.signal(sig, handler)
    elapsed = time.monotonic() - started
    tasks, commands = terminal_claims(root, wrapper_id, child.pid, elapsed, claims_dir)
    terminal = {"schema": "AIC_FINAL_OWNED_WRAPPER_V1", "owned_wrapper_id": wrapper_id,
                "asset_lock": ref(args.assets), "child_exit_code": code, "work_terminated": True,
                "termination_basis": "owned_wrapper_terminal", "no_external_task_signaled": True,
                "stopped_owned_process": stopped, "stop_reason": stop_reason,
                "wall_seconds_including_load_decode_failures": elapsed,
                "command_log": ref(directory / "command.log"), "task_terminals": tasks,
                "command_terminals": commands, "finished_at": utc_now()}
    result_ref = atomic_new(directory / "completion.json", terminal)
    import json
    print(json.dumps({"status": "OWNED_WRAPPER_TERMINAL", "exit_code": code,
                      "completion": result_ref, "wall_seconds": elapsed}), flush=True)
    return code if code is not None and 0 <= code <= 125 else 1


if __name__ == "__main__":
    raise SystemExit(main())
