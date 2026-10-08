"""Single registered background continuation. No scientific retuning on test."""
import datetime as dt
import fcntl
import json
import os
import socket
from pathlib import Path
import subprocess
import sys
import traceback
import runtime as rt
import experiment as ex
import context_contract as cc

PY = Path("/home/inspur/aic_video_work/env/qwen3vl_isolated_20260910/bin/python")
PREFIX = "aic_CAD_v1_"


def utc():
    return dt.datetime.now(dt.timezone.utc).isoformat()


def state(stage, **data):
    ex.progress(rt.HERE / "progress.json", dict(stage=stage, utc=utc(), pid=os.getpid(),
        new_training_updates=0, official_score=None, uploaded=False, automatic_return=False, **data))


def cpu(name, args):
    ex.verify(); state("RUNNING_CPU_" + name.upper())
    with (rt.HERE / (name + ".cpu.log")).open("x") as log:
        result = subprocess.run([str(PY), "-B", *map(str, args)], stdout=log, stderr=subprocess.STDOUT,
            stdin=subprocess.DEVNULL, cwd=rt.RUN)
    cc.require(result.returncode == 0, "CPU stage failed: " + name)


def gpu(name, args, maximum, planned):
    ex.verify(); state("RUNNING_GPU_" + name.upper(), single_job_maximum_seconds=maximum,
        remaining_output_estimate_bytes=planned)
    runname = PREFIX + name
    with (rt.HERE / (name + ".wrapper.log")).open("x") as log:
        result = subprocess.run([str(PY), "-B", str(rt.RUN / "resource_unlimited_v1_20261007/gpu_run.py"),
            "--name", runname, "--max-seconds", str(maximum), "--planned-output-bytes", str(planned),
            "--capacity-reason", "Frozen C-advisory control receipts and existing source files; no saved video/weights; actual capacity and shared-conflict checks",
            "--queue-seconds", str(3 * 86400), "--", str(PY), "-B", *map(str, args)],
            stdout=log, stderr=subprocess.STDOUT, stdin=subprocess.DEVNULL, cwd=rt.RUN)
    path = rt.RUN / "controller" / (runname + ".resource.json")
    cc.require(result.returncode == 0 and path.is_file(), "owned GPU stage stopped: " + name)
    receipt = ex.read(path)
    cc.require(receipt["status"] == "completed" and receipt["exit_code"] == 0 and receipt["stop_reason"] is None,
        "GPU stage not successfully accounted: " + name)
    return {"path": str(path), "sha256": ex.sha(path), "charged_seconds": receipt["charged_seconds"]}


def main():
    cc.require(socket.gethostname() == "inspur-NP5570M5", "wrong production host")
    lock = (rt.HERE / "controller.lock").open("a")
    fcntl.flock(lock, fcntl.LOCK_EX | fcntl.LOCK_NB)
    cc.require(not (rt.HERE / "registration.json").exists(), "controller already registered; do not relaunch")
    ex.verify()
    rt.raw_write(rt.HERE / "registration.json", {"utc": utc(), "pid": os.getpid(), "pgid": os.getpgrp(),
        "command": sys.argv, "source_lock_sha256": ex.sha(rt.HERE / "source_lock.json"), "model_calls_at_start": 0})
    charges = {}
    try:
        charges["nontest"] = gpu("nontest", [rt.HERE / "experiment.py", "nontest"], 7200, 100 << 20)
        cpu("nontest_mechanism", [rt.HERE / "report.py", "nontest"])
        cpu("nontest_assemble", [rt.HERE / "packager.py", "assemble", "nontest"])
        cpu("nontest_finish", [rt.HERE / "packager.py", "finish", "nontest"])
        charges["pilot"] = gpu("pilot", [rt.HERE / "experiment.py", "pilot"], 14400, 300 << 20)
        cpu("pilot_report", [rt.HERE / "report.py", "pilot"])
        # Pre-authorized expansion. No pilot weak score or changing sample gate.
        charges["full"] = gpu("full", [rt.HERE / "experiment.py", "full"], 28800, 1200 << 20)
        cpu("full_report", [rt.HERE / "report.py", "full"])
        decision = ex.read(rt.HERE / "developer_01/full.report.json")
        if decision["status"] != "GO_ONE_FROZEN_C_EXPLORATION_PACKAGE":
            state("C_INVESTMENT_STOP_CONTINUING_NONTEST_FALLBACK", decision=decision, resources=charges)
            cpu("fallback_inventory", [rt.HERE / "fallback.py", "inventory"])
            rt.raw_write(rt.HERE / "scientific_stop.json", {"utc": utc(), "C": decision, "resources": charges,
                "next": "MONITOR_IMPLEMENT_MATCHED_B_BOUNDARY_DIAGNOSTIC_PER_FALLBACK_RECEIPT",
                "not_a_final_ZIP": True, "user_confirmation_required": False})
            state("WAITING_AGENT_CONCRETE_B_BOUNDARY_CONTINUATION", resources=charges)
            return
        # New source planning for test is only admitted after the frozen
        # non-test rule. Only R is run; null/shuffle never enter test production.
        cpu("rematch_prepare", [rt.HERE / "experiment.py", "prepare-rematch"])
        charges["rematch"] = gpu("rematch", [rt.HERE / "experiment.py", "rematch"], 43200, 2000 << 20)
        cpu("rematch_assemble", [rt.HERE / "packager.py", "assemble", "rematch"])
        cpu("rematch_finish", [rt.HERE / "packager.py", "finish", "rematch"])
        cpu("independent_final", [rt.HERE / "final_acceptance.py"])
        accepted = ex.read(rt.HERE / "final_acceptance.json")
        cc.require(accepted["status"] == "PASS_INDEPENDENT_C_ADVISORY_FINAL", "independent final did not pass")
        rt.raw_write(rt.HERE / "completion.json", dict(accepted, status="PASS_COMPLETE_426_C_ADVISORY_ZIP_ON_LINUX",
            utc=utc(), resources=charges, source_lock_sha256=ex.sha(rt.HERE / "source_lock.json")))
        state("PASS_COMPLETE_426_C_ADVISORY_ZIP_ON_LINUX", candidate=accepted["candidate"])
    except BaseException as error:
        rt.raw_write(rt.HERE / "execution_failure.json", {"utc": utc(), "status": "STOP_ENGINEERING_FAILURE_PRESERVED",
            "error": type(error).__name__ + ": " + str(error), "traceback": traceback.format_exc(), "resources_completed": charges,
            "next": "AGENT_REPRODUCE_THEN_NEW_VERSION_EXACT_SUCCESS_REUSE", "old_frozen_source_unchanged": True})
        state("STOP_ENGINEERING_FAILURE_AGENT_MUST_REPAIR", error=str(error))
        raise


if __name__ == "__main__":
    main()
