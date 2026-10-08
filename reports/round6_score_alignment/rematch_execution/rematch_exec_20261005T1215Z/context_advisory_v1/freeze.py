"""Freeze once, after completed actual CPU draft acceptance; no launcher."""
import json
import socket
from pathlib import Path
import runtime as rt
import experiment as ex
import context_contract as cc


def main():
    cc.require(socket.gethostname() == "inspur-NP5570M5", "wrong freeze host")
    cc.require(not (rt.HERE / "source_lock.json").exists(), "source already frozen")
    draft = ex.read(rt.HERE / "draft_preflight.json")
    cc.require(draft["status"] == "PASS_REAL_CPU_NATIVE_PROCESSOR_CONTRACTS_NO_GPU_CALLS" and
        len(draft["non_test_proofs"]) == 8 and draft["model_calls"] == 0, "real draft CPU proof incomplete")
    old_lock_path = rt.RUN / "teacher_student_autopilot_v14/source_lock.json"
    engineering = ex.read(rt.HERE / "cpu_build_acceptance.json")
    cc.require(engineering['status'] == 'PASS_CPU_ENGINEERING_GATES_AND_ACTUAL_MODULE_BINDING', 'downstream CPU acceptance missing')
    for p, wanted in engineering['processor_code_bindings'].items():
        cc.require(ex.sha(p) == wanted, 'accepted processor code changed')
    old_lock = ex.read(old_lock_path)
    files = dict(old_lock["files"])
    files[str(old_lock_path)] = ex.sha(old_lock_path)
    # Retain all old byte bindings, including actual native/precision/cache
    # dependencies. This is a hash check, not a repeat of old model acceptance.
    for path, wanted in files.items():
        cc.require(ex.sha(path) == wanted, "old frozen dependency changed: " + path)
    for path in rt.HERE.iterdir():
        if path.is_file() and path.suffix in (".py", ".md"):
            files[str(path)] = ex.sha(path)
    for path in (rt.HERE / "input_01").rglob('*'):
        if path.is_file():
            files[str(path)] = ex.sha(path)
    files[str(rt.HERE / "draft_preflight.json")] = ex.sha(rt.HERE / "draft_preflight.json")
    files[str(rt.HERE / "cpu_build_acceptance.json")] = ex.sha(rt.HERE / "cpu_build_acceptance.json")
    lock = {"schema": "AIC_CONTEXT_ADVISORY_EXACT_V1", "files": files,
        "old_dependency_lock_sha256": ex.sha(old_lock_path), "discussion_final_sha256":
        "05fc69da7f19a1a64faf5c8d469237d40d4aaffaae05690c271d03564332c390",
        "discussion_final_metadata_sha256": "586d95e6a92c4b17008d9c60c6d30aeff0fe69f51ecb5eb082af3f8221875765",
        "metadata_addendum_before_first_model_call": "104_FILES_96_GROUPS_NO_CROSS_FILE_OVERVIEW_UNION",
        "model_calls_at_freeze": 0, "optimizer_updates_at_freeze": 0}
    rt.raw_write(rt.HERE / "source_lock.json", lock)
    # Actual CPU tensors already accepted in this unchanged draft. Copy the
    # proof with its new frozen lock reference; do not claim a new processor run.
    rt.raw_write(rt.HERE / "preflight.json", dict(draft, source_lock_sha256=ex.sha(rt.HERE / "source_lock.json"),
        original_cpu_proof_sha256=ex.sha(rt.HERE / "draft_preflight.json"),
        frozen_binding_verified=True, original_cpu_proof_reused=True, new_processor_calls=0))
    print(json.dumps({"status": "PASS_FROZEN_AFTER_ACTUAL_CPU_PREFLIGHT", "files": len(files),
        "source_lock_sha256": ex.sha(rt.HERE / "source_lock.json"), "new_model_calls": 0}), flush=True)


if __name__ == "__main__":
    main()
