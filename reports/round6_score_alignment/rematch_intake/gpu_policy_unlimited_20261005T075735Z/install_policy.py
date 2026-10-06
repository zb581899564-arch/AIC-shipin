"""Install only the current cumulative-time policy; no workload is launched."""
import datetime as dt
import fcntl
import hashlib
import json
from pathlib import Path
import shutil
import subprocess

HERE = Path(__file__).resolve().parent
ROOT = Path("/home/inspur/aic_video_work")
CAMPAIGN = ROOT / "improvement_round1"
RUNNER = CAMPAIGN / "budget_run.py"
COORDINATION = ROOT / "coordination.json"
LEDGER = CAMPAIGN / "gpu_ledger.jsonl"
POLICY = ROOT / "resource_policy.json"


def digest(path):
    return hashlib.sha256(path.read_bytes()).hexdigest()


def atomic_bytes(path, raw, mode=None):
    temp = path.with_name(path.name + ".policy-update.tmp")
    with temp.open("xb") as out:
        out.write(raw)
    if mode is not None:
        temp.chmod(mode)
    temp.replace(path)


if __name__ == "__main__":
    assert subprocess.check_output(["hostname"], text=True).strip() == "inspur-NP5570M5"
    with (CAMPAIGN / "gpu.lock").open("a") as lock:
        fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
        assert not (CAMPAIGN / "active_gpu_job.json").exists(), "active job present"
        gpu = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
            text=True).strip()
        assert not gpu, "GPU is occupied"
        assert digest(RUNNER) == digest(HERE / "before/budget_run.py"), "runner changed"
        assert digest(COORDINATION) == digest(HERE / "before/coordination.json"), "coordination changed"
        assert not POLICY.exists(), "resource policy already exists; do not replace blindly"
        ledger_before = digest(LEDGER)
        records = [json.loads(line) for line in LEDGER.read_text().splitlines() if line]
        policy = json.loads((HERE / "resource_policy.json").read_text())
        assert policy["gpu_time_mode"] == "UNLIMITED"
        assert policy["max_total_gpu_seconds"] is None
        assert policy["ledger_initial_charge_seconds"] == 7200
        coordination = json.loads(COORDINATION.read_text())
        before_gpu_budget_hours = coordination["gpu_budget_hours"]
        coordination["gpu_budget_hours"] = None
        coordination["gpu_time_mode"] = "UNLIMITED"
        coordination["resource_policy_path"] = str(POLICY)
        coordination["gpu_policy_updated_utc"] = dt.datetime.now(dt.timezone.utc).isoformat()
        updated_coordination = json.dumps(coordination, ensure_ascii=False, indent=2) + "\n"
        compile((HERE / "budget_run.py").read_text(), str(RUNNER), "exec")
        atomic_bytes(POLICY, (HERE / "resource_policy.json").read_bytes(), 0o644)
        atomic_bytes(COORDINATION, updated_coordination.encode("utf-8"),
                     COORDINATION.stat().st_mode & 0o777)
        atomic_bytes(RUNNER, (HERE / "budget_run.py").read_bytes(), RUNNER.stat().st_mode & 0o777)
        subprocess.run(["python3", "-B", str(HERE / "test_resource_policy.py"), str(RUNNER)],
                       check=True)
        assert ledger_before == digest(LEDGER), "ledger unexpectedly changed"
        assert not (CAMPAIGN / "active_gpu_job.json").exists()
        gpu_after = subprocess.check_output(
            ["nvidia-smi", "--query-compute-apps=pid,process_name", "--format=csv,noheader"],
            text=True).strip()
        result = dict(status="APPLIED_VERIFIED_CPU_ONLY",
                      installed_utc=dt.datetime.now(dt.timezone.utc).isoformat(),
                      gpu_time_mode="UNLIMITED", max_total_gpu_seconds=None,
                      old_gpu_budget_hours=before_gpu_budget_hours,
                      ledger_sha256_before=ledger_before, ledger_sha256_after=digest(LEDGER),
                      ledger_rows=len(records),
                      cumulative_charged_seconds=7200 + sum(r["charged_seconds"] for r in records),
                      runner_sha256=digest(RUNNER), policy_sha256=digest(POLICY),
                      coordination_sha256=digest(COORDINATION),
                      gpu_compute_before=gpu, gpu_compute_after=gpu_after,
                      free_bytes=shutil.disk_usage(ROOT).free,
                      new_gpu_jobs_started=0, tests_passed=9)
        (HERE / "install_result.json").write_text(json.dumps(result, indent=2) + "\n")
        shutil.copyfile(COORDINATION, HERE / "coordination_after.json")
        print(json.dumps(result))
