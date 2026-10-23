"""Finite shared Linux resource accounting, independent of old experiment gates."""
from __future__ import annotations

from contextlib import contextmanager
from datetime import datetime, timezone
import fcntl
import math
import os
from pathlib import Path
import shutil
import socket
import subprocess
import time
import uuid

from .contracts import atomic_new, checked, ref, require, strict_load, utc_now


def _run(args):
    return subprocess.check_output(args, text=True, timeout=15).strip()


def _positive_int(value, name, *, zero=False):
    require(type(value) is int and value >= (0 if zero else 1), "Invalid resource limit: " + name)
    return value


def _limits(assets):
    cfg = assets["resources"]
    for name in ("planned_output_bytes", "planned_scratch_bytes", "disk_reserve_bytes",
                 "required_gpu_memory_bytes", "finalization_reserve_seconds"):
        _positive_int(cfg[name], name)
    _positive_int(cfg["cpu_threads"], "cpu_threads")
    require(cfg["cpu_threads"] <= 2, "Protect the existing Java CPU task: at most2 threads")
    _positive_int(cfg["gpu_index"], "gpu_index", zero=True)
    for name, default in (("ram_reserve_bytes", 2 << 30), ("planned_ram_bytes", cfg["planned_scratch_bytes"]),
                          ("total_execution_seconds", 18 * 3600)):
        _positive_int(cfg.get(name, default), name)
    require(cfg.get("total_execution_seconds", 18 * 3600) <= 18 * 3600,
            "Final sprint execution budget may not exceed18h")
    return cfg


def _memory_available():
    values = {}
    for line in Path("/proc/meminfo").read_text().splitlines():
        key, value = line.split(":", 1)
        values[key] = value.strip()
    require("MemAvailable" in values, "Actual Linux MemAvailable is required")
    return int(values["MemAvailable"].split()[0]) * 1024


def snapshot(assets, *, require_gpu=False):
    root = Path(assets["run_root"])
    ancestor = root
    while not ancestor.exists():
        ancestor = ancestor.parent
    cfg = _limits(assets)
    disk = shutil.disk_usage(ancestor)
    scratch = Path(cfg["scratch_dir"]).resolve(strict=True)
    require(scratch.is_dir(), "Existing scratch directory required")
    scratch_usage = shutil.disk_usage(scratch)
    same_filesystem = ancestor.stat().st_dev == scratch.stat().st_dev
    output_peak = cfg["planned_output_bytes"] + cfg["disk_reserve_bytes"]
    if same_filesystem:
        output_peak += cfg["planned_scratch_bytes"]
    require(disk.free >= output_peak,
            "Insufficient actual combined output/scratch filesystem capacity; bind an existing approved data filesystem")
    require(scratch_usage.free >= cfg["planned_scratch_bytes"], "Scratch/tmpfs capacity insufficient")
    memory = _memory_available()
    require(memory >= cfg.get("planned_ram_bytes", cfg["planned_scratch_bytes"]) + cfg.get("ram_reserve_bytes", 2 << 30),
            "Insufficient current MemAvailable after Java/other-task reserve; tmpfs capacity is not free physical RAM")
    now = datetime.now(timezone.utc)
    deadline = datetime.fromisoformat(assets["deadline"].replace("Z", "+00:00"))
    require(deadline.tzinfo is not None, "Timezone-aware deadline required")
    remaining = (deadline - now).total_seconds()
    require(remaining > cfg["finalization_reserve_seconds"], "Only finalization reserve remains")
    result = {"time": utc_now(), "output_free_bytes": disk.free,
              "scratch_free_bytes": scratch_usage.free, "same_output_scratch_filesystem": same_filesystem,
              "combined_output_peak_bytes": output_peak, "mem_available_bytes": memory,
              "ram_reserve_bytes": cfg.get("ram_reserve_bytes", 2 << 30),
              "remaining_seconds": remaining, "cpu_threads": cfg["cpu_threads"], "no_process_signals": True}
    try:
        result["gpus"] = _run(["nvidia-smi", "--query-gpu=index,uuid,memory.total,memory.free,utilization.gpu",
                               "--format=csv,noheader,nounits"])
        result["gpu_processes"] = _run(["nvidia-smi", "--query-compute-apps=gpu_uuid,pid,used_memory",
                                        "--format=csv,noheader,nounits"])
    except (OSError, subprocess.SubprocessError):
        require(not require_gpu, "Real Linux NVIDIA device required; CPU checks are not production")
        result.update(gpus="UNAVAILABLE", gpu_processes="UNAVAILABLE")
    if require_gpu:
        devices = [line.split(",") for line in result["gpus"].splitlines()]
        selected = [parts for parts in devices if parts[0].strip() == str(cfg["gpu_index"])]
        require(len(selected) == 1 and len(selected[0]) == 5, "Explicit GPU index unavailable")
        device = selected[0]
        require(float(device[3]) * (1 << 20) >= cfg["required_gpu_memory_bytes"],
                "Shared GPU has insufficient current free memory; defer without taking other jobs' memory")
        device_uuid = device[1].strip()
        foreign = [line for line in result["gpu_processes"].splitlines()
                   if line.split(",")[0].strip() == device_uuid and line.split(",")[1].strip() != str(os.getpid())]
        if foreign:
            grant_ref = cfg.get("shared_gpu_grant")
            require(grant_ref, "Foreign GPU task active: use existing shared scheduler or defer")
            grant = strict_load(checked(grant_ref))
            require(grant.get("status") == "GRANTED" and grant.get("gpu_uuid") == device_uuid and
                    grant.get("run_root") == assets["run_root"] and
                    isinstance(grant.get("reservation_id"), str) and grant["reservation_id"],
                    "Shared GPU grant does not authorize this exact run")
            issued = datetime.fromisoformat(grant["issued_at"].replace("Z", "+00:00"))
            expires = datetime.fromisoformat(grant["expires_at"].replace("Z", "+00:00"))
            require(issued.tzinfo is not None and expires.tzinfo is not None and issued <= now < expires,
                    "Shared GPU scheduler grant is not currently valid")
            result["shared_scheduler_reservation"] = {"reservation_id": grant["reservation_id"],
                "grant_ref": grant_ref, "expires_at": grant["expires_at"]}
        result["gpu_uuid"] = device_uuid
    return result


@contextmanager
def gpu_lease(assets):
    """Serialize this sprint's processes; never signal an unrelated process."""
    root = Path(assets["run_root"])
    root.mkdir(parents=True, exist_ok=True)
    with (root / "gpu.lock").open("a+b") as stream:
        try:
            fcntl.flock(stream.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError as error:
            raise RuntimeError("Another sprint GPU command owns the lease") from error
        try:
            yield snapshot(assets, require_gpu=True)
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


@contextmanager
def _accounting_lock(root):
    root.mkdir(parents=True, exist_ok=True)
    with (root / "ledger.lock").open("a+b") as stream:
        fcntl.flock(stream.fileno(), fcntl.LOCK_EX)
        try:
            yield
        finally:
            fcntl.flock(stream.fileno(), fcntl.LOCK_UN)


def _replace_index(path, value):
    temporary = path.with_name(path.name + ".partial-" + uuid.uuid4().hex)
    atomic_new(temporary, value)
    os.replace(temporary, path)
    descriptor = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(descriptor)
    finally:
        os.close(descriptor)


def _command_ids(directory):
    """Include durable claims even if death interrupted the following index write.

    This scans only exact claim files in this sprint's accounting directory,
    never model/assets or a latest experiment. An orphan reserves its entire
    cap until its owned wrapper terminal is reconciled.
    """
    index_path = directory / "index.json"
    identifiers = strict_load(index_path)["command_ids"] if index_path.exists() else []
    require(isinstance(identifiers, list) and len(set(identifiers)) == len(identifiers),
            "Command cost registry duplicated or malformed")
    orphan_ids = []
    for path in sorted(directory.glob("*/claim.json")):
        command_id = path.parent.name
        claim = strict_load(path)
        require(claim.get("command_id") == command_id, "Durable command claim identity differs")
        if command_id not in identifiers:
            orphan_ids.append(command_id)
    return identifiers + orphan_ids


def _command_totals(directory, *, exclude=None):
    identifiers = _command_ids(directory)
    confirmed, unresolved, open_commands = 0.0, 0.0, []
    for command_id in identifiers:
        require(isinstance(command_id, str) and len(command_id) == 32 and
                all(c in "0123456789abcdef" for c in command_id), "Invalid registered command ID")
        if command_id == exclude:
            continue
        folder = directory / command_id
        claim = strict_load(folder / "claim.json")
        require(claim["command_id"] == command_id, "Command claim identity differs")
        terminal = folder / "completion.json"
        if terminal.exists():
            value = strict_load(terminal)
            seconds = value["wall_seconds_including_load_decode_failures"]
            require(value["command_id"] == command_id and type(seconds) in (float, int) and
                    math.isfinite(seconds) and seconds >= 0, "Command terminal accounting malformed")
            confirmed += seconds
        else:
            # It is a reservation, not an invented actual GPU charge. A killed
            # command is resolved only from its owned wrapper terminal.
            cap = claim["cap_seconds"]
            require(type(cap) in (int, float) and math.isfinite(cap) and cap > 0,
                    "Unresolved command cap must be finite and positive")
            unresolved += cap
            open_commands.append(command_id)
    return {"confirmed_command_wall_seconds": confirmed,
            "unresolved_reserved_seconds": unresolved, "unresolved_command_ids": open_commands,
            "accounting_scope": "exclusive owned model-command wall; per-source receipts are not summed again"}


def cumulative_execution(assets):
    directory = Path(assets["run_root"]) / "command_budget"
    with _accounting_lock(directory):
        result = _command_totals(directory)
    result["total_execution_seconds"] = _limits(assets).get("total_execution_seconds", 18 * 3600)
    return result


class Budget:
    """Charge one whole command, including load/decode/failure; avoid task double-counts.

    Use as a context manager or call finish() in a finally block. A receipt()
    snapshot alone is not a terminal. An unresolved process reserves its entire
    cap until the exact owned-wrapper terminal reconciles it.
    """
    def __init__(self, assets, stage, cap_seconds):
        require(type(cap_seconds) in (int, float) and math.isfinite(cap_seconds) and cap_seconds > 0,
                "Finite positive stage wall budget required")
        self.assets, self.stage = assets, stage
        now_monotonic = time.monotonic()
        self.started = now_monotonic
        if os.environ.get("AIC_FINAL_WRAPPER_ID"):
            origin = float(os.environ["AIC_FINAL_COMMAND_STARTED_MONOTONIC"])
            require(math.isfinite(origin) and 0 <= origin <= now_monotonic,
                    "Owned-wrapper command start must be an actual earlier monotonic instant")
            self.started = origin
        self.calls = 0
        self.command_id = uuid.uuid4().hex
        self.directory = Path(assets["run_root"]) / "command_budget"
        self.terminal = None
        cfg = _limits(assets)
        with _accounting_lock(self.directory):
            prior = _command_totals(self.directory)
            available = cfg.get("total_execution_seconds", 18 * 3600) - prior["confirmed_command_wall_seconds"] - prior["unresolved_reserved_seconds"]
            require(available > 0, "Cumulative model-command budget exhausted or reserved by unresolved work")
            self.cap = min(float(cap_seconds), available)
            self.folder = self.directory / self.command_id
            self.folder.mkdir()
            atomic_new(self.folder / "claim.json", {"command_id": self.command_id, "stage": stage,
                "cap_seconds": self.cap, "started_at": utc_now(), "pid": os.getpid(),
                "host": socket.gethostname(), "pid_is_not_restart_authority": True,
                "owned_wrapper_id": os.environ.get("AIC_FINAL_WRAPPER_ID"),
                "run_root": assets["run_root"]})
            index_path = self.directory / "index.json"
            index = {"command_ids": _command_ids(self.directory)}
            _replace_index(index_path, index)

    def __enter__(self):
        try:
            self.check()
        except BaseException as error:
            self.finish("FAILED", error=error)
            raise
        return self

    def __exit__(self, kind, error, traceback):
        self.finish("FAILED" if error is not None else "SUCCESS", error=error)
        return False

    def check(self, estimated_next_seconds=0):
        require(type(estimated_next_seconds) in (float, int) and math.isfinite(estimated_next_seconds) and
                estimated_next_seconds >= 0, "Finite nonnegative next-work estimate required")
        require(self.terminal is None, "A completed command cannot perform additional work")
        elapsed = time.monotonic() - self.started
        deadline = datetime.fromisoformat(self.assets["deadline"].replace("Z", "+00:00"))
        left = (deadline - datetime.now(timezone.utc)).total_seconds()
        cfg = self.assets["resources"]
        reserve = cfg["finalization_reserve_seconds"]
        require(shutil.disk_usage(self.assets["run_root"]).free >= cfg["disk_reserve_bytes"] + (16 << 20),
                "Stop before the next model/source result would consume the protected disk reserve")
        require(elapsed + estimated_next_seconds < self.cap, "Stage wall-time budget exhausted")
        require(left > reserve + estimated_next_seconds, "Do not consume finalization/transfer/platform reserve")
        with _accounting_lock(self.directory):
            prior = _command_totals(self.directory, exclude=self.command_id)
        require(prior["confirmed_command_wall_seconds"] + prior["unresolved_reserved_seconds"] + elapsed + estimated_next_seconds
                < cfg.get("total_execution_seconds", 18 * 3600), "Cumulative18h command budget exhausted")
        return elapsed

    def receipt(self):
        if self.terminal is not None:
            return self.terminal
        return {"command_id": self.command_id, "stage": self.stage,
                "wall_seconds_including_load_decode_failures": time.monotonic() - self.started,
                "physical_model_calls": self.calls, "cap_seconds": self.cap,
                "actual_gpu_kernel_seconds": "NOT_INDEPENDENTLY_METERED",
                "cost_basis": "Owned Linux; no purchased resources or external inference"}

    def finish(self, status="SUCCESS", *, error=None):
        require(status in {"SUCCESS", "FAILED", "STOPPED"}, "Explicit command terminal required")
        if self.terminal is not None:
            return self.terminal
        result = dict(self.receipt(), status=status, finished_at=utc_now(),
                      error_type=type(error).__name__ if error is not None else None,
                      error=str(error) if error is not None else None)
        with _accounting_lock(self.directory):
            path = self.folder / "completion.json"
            if path.exists():
                result = strict_load(path)
            else:
                atomic_new(path, result)
        self.terminal = result
        return result


def resolve_command_budget(assets, command_id, wrapper_terminal_ref):
    """Reconcile a killed owned command from its exact wrapper terminal, never PID age."""
    directory = Path(assets["run_root"]) / "command_budget"
    with _accounting_lock(directory):
        require(command_id in _command_ids(directory), "Unknown cost claim")
        folder = directory / command_id
        if (folder / "completion.json").exists():
            return strict_load(folder / "completion.json")
        claim = strict_load(folder / "claim.json")
        proof = strict_load(checked(wrapper_terminal_ref))
        require(proof.get("command_id") == command_id and proof.get("work_terminated") is True and
                proof.get("termination_basis") == "owned_wrapper_terminal" and
                proof.get("no_external_task_signaled") is True and
                proof.get("claim_sha256") == ref(folder / "claim.json")["sha256"],
                "Exact owned wrapper-terminal accounting proof required")
        if claim.get("owned_wrapper_id") is not None:
            require(proof.get("owned_wrapper_id") == claim["owned_wrapper_id"],
                    "Cost terminal came from a different owned wrapper")
        seconds = proof.get("wall_seconds_including_load_decode_failures")
        require(type(seconds) in (float, int) and math.isfinite(seconds) and seconds >= 0,
                "Actual wrapper-measured command wall seconds required")
        result = {"command_id": command_id, "stage": claim["stage"], "status": "RECONCILED_TERMINATED",
                  "wall_seconds_including_load_decode_failures": seconds,
                  "wrapper_terminal_ref": wrapper_terminal_ref, "finished_at": utc_now(),
                  "actual_gpu_kernel_seconds": "NOT_INDEPENDENTLY_METERED", "no_new_model_calls": True}
        atomic_new(folder / "completion.json", result)
        return result
