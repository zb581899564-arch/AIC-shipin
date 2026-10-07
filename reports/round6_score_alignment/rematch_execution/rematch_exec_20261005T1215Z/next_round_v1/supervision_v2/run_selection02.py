"""Once-only detached CPU selection02; no model imports or GPU jobs."""
import argparse
import datetime as dt
import hashlib
import json
import os
from pathlib import Path
import shutil
import socket
import subprocess
import sys

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/inspur/aic_video_work")
R7 = ROOT / "round6_score_alignment/r7_temporal_pool/round7_temporal_pool_20260921T090903Z/inputs"
LINUX_QUOTA = 51 * 2**30
COMBINED_CAP = 80 * 2**30
PLANNED_OUTPUT = 8 * 2**20


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def sha(path):
    return hashlib.sha256(Path(path).read_bytes()).hexdigest()


def save(path, value):
    temporary = Path(str(path) + ".tmp")
    temporary.write_text(json.dumps(value, indent=2, ensure_ascii=False) + "\n", encoding="utf-8")
    temporary.replace(path)


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--source-lock-sha256", required=True)
    args = parser.parse_args()
    if socket.gethostname() != "inspur-NP5570M5" or HERE.parent.name != "next_round_v1" or HERE.name != "supervision_v2":
        raise RuntimeError("wrong host or independent v2 directory")
    lock = HERE / "source_lock_02.json"
    if sha(lock) != args.source_lock_sha256:
        raise RuntimeError("v2 CPU source lock identity differs")
    spec = json.loads(lock.read_text(encoding="utf-8"))
    for name, digest in spec["files"].items():
        if sha(HERE / name) != digest:
            raise RuntimeError("bound v2 preparation bytes changed: " + name)
    for name, digest in spec.get("readonly_compatibility_test_dependencies", {}).items():
        if sha(HERE / name) != digest:
            raise RuntimeError("unchanged teacher compatibility dependency changed: " + name)
    if (HERE / "selection_02").exists() or (HERE / "selection02_registration_01.json").exists():
        raise RuntimeError("selection02 already registered/output exists; never restart")
    state = {"schema": "aic_selection02_cpu_registration_v1", "registered_utc": utc(),
        "controller_pid": os.getpid(), "hostname": socket.gethostname(), "source_lock_sha256": args.source_lock_sha256,
        "gpu_used": False, "models_loaded": False, "status": "CPU_PREFLIGHT", "counts": {"train": 0, "dev": 0}}
    registration = HERE / "selection02_registration_01.json"
    with registration.open("x", encoding="utf-8") as stream:
        stream.write(json.dumps(state, indent=2) + "\n")
    latest = HERE / "selection02_latest_01.json"
    completion = HERE / "selection02_completion_01.json"
    try:
        evidence = json.loads((HERE / "capacity_transfer_01.json").read_text(encoding="utf-8"))
        mac_bytes = evidence["mac_work_bytes"]
        measured = dt.datetime.fromisoformat(evidence["recorded_after_readonly_queries_utc"])
        if evidence["mac_hostname"] != "choubkdeMac-Mini.local" or (dt.datetime.now(dt.timezone.utc) - measured).total_seconds() > 900:
            raise RuntimeError("fresh approved Mac preflight snapshot missing")
        linux_bytes = int(subprocess.check_output(["du", "-s", "-B1", str(ROOT)], text=True).split()[0])
        free_bytes = shutil.disk_usage(ROOT).free
        if linux_bytes + PLANNED_OUTPUT > LINUX_QUOTA or linux_bytes + mac_bytes + PLANNED_OUTPUT > COMBINED_CAP or free_bytes < PLANNED_OUTPUT:
            raise RuntimeError("live Linux51GiB/combined80GiB output admission failed")
        state.update(status="CPU_CONTRACT_TESTS", resource={"checked_utc": utc(), "linux_work_bytes": linux_bytes,
            "mac_work_bytes": mac_bytes, "planned_output_bytes": PLANNED_OUTPUT, "linux_quota_bytes": LINUX_QUOTA,
            "combined_cap_bytes": COMBINED_CAP, "free_bytes": free_bytes})
        save(latest, state)
        with (HERE / "cpu_linux_tests_01.log").open("x", encoding="utf-8") as log:
            subprocess.run([sys.executable, "-B", str(HERE / "test_selector_cpu.py"), "--receipt", str(HERE / "cpu_linux_result_01.json")],
                           stdout=log, stderr=subprocess.STDOUT, check=True, timeout=60)
        state.update(status="CPU_SELECTING_128_TRAIN_32_DEV", updated_utc=utc())
        save(latest, state)
        command = [sys.executable, "-B", str(HERE / "select_windows.py"), "--train-manifest", str(R7 / "train_temporal.jsonl"),
            "--dev-manifest", str(R7 / "dev_temporal.jsonl"), "--ffprobe", "/home/inspur/anaconda3/envs/Andy/bin/ffprobe",
            "--tier", "first", "--out-dir", str(HERE / "selection_02")]
        child = subprocess.Popen(command, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True, bufsize=1)
        state["selector_pid"] = child.pid
        save(latest, state)
        for line in child.stdout:
            print(line, end="", flush=True)
            try:
                event = json.loads(line)
            except (ValueError, TypeError):
                continue
            if event.get("split") in ("train", "dev") and type(event.get("completed")) is int:
                state["counts"][event["split"]] = event["completed"]
                state["updated_utc"] = utc()
                save(latest, state)
        code = child.wait()
        if code != 0:
            raise RuntimeError("selector failed exit " + str(code))
        receipt = HERE / "selection_02/selection_receipt.json"
        result = json.loads(receipt.read_text(encoding="utf-8"))
        if result["status"] != "PASS_CPU_SELECTION_UNLABELLED" or result["counts"] != {"train": 128, "dev": 32}:
            raise RuntimeError("exact full CPU selection acceptance failed")
        state.update(status="PASS_CPU_SELECTION02_UNLABELLED_128_32", completed_utc=utc(),
            counts=result["counts"], selection_receipt_sha256=sha(receipt),
            cpu_contract_result_sha256=sha(HERE / "cpu_linux_result_01.json"), labels_generated=False)
    except Exception as exc:
        state.update(status="STOP_CPU_SELECTION02", completed_utc=utc(), reason=f"{type(exc).__name__}: {exc}")
        save(latest, state)
        save(completion, state)
        raise
    save(latest, state)
    save(completion, state)
    print(json.dumps(state, ensure_ascii=False), flush=True)


if __name__ == "__main__":
    main()
