"""C's own native temporal assembly and independent complete ZIP acceptance."""
import argparse
import json
from pathlib import Path
import subprocess
import sys
import zipfile
import context_contract as cc
import runtime as rt
import experiment as ex


def assemble(scope):
    ex.verify()
    student, old, frames, production = rt.bind_helpers()
    plan = ex.read(rt.HERE / "input_01" / (scope + "_plan.json"))
    out = rt.HERE / (scope + "_01")
    terminal = ex.read(out / (scope + ".completion.json"))
    cc.require(terminal["status"] == "PASS_ALL_REGISTERED_ADVISORY_ATTEMPTS" and terminal["records"] == (8 if scope == "nontest" else 426), "scope generation not complete")
    rows = []
    for job in plan["jobs"]:
        item = job["metadata"]
        record = dict(video_id=job["video_id"], targetRatioWH=item["targetRatioWH"], video_path=item["source_path"],
            n_frames=item["n_frames"], fps=item["fps_num"] / item["fps_den"],
            arm="C_ADVISORY_BASE_OVERVIEW_B_LOCAL_ALL_NATIVE_WINDOWS", windows=[])
        table_path = out / "overview" / job["source_key"] / "done.json"
        table = ex.read(table_path)
        cc.require(table["output_valid"] is True and table["overview_window"]["source_sha256"] == job["source_key"], "overview identity/validity missing")
        cc.validate_overview(table["raw_output"], table["overview_window"]["planned_actual_pts_sec"])
        for p, wanted in table["bound_files"].items():
            cc.require(ex.sha(p) == wanted, "overview original raw differs")
        for ix, part in enumerate(job["windows"]):
            path = out / "local" / cc.digest(job["video_id"]) / str(ix) / "R/done.json"
            value = ex.read(path)
            for p, wanted in value["bound_files"].items():
                cc.require(ex.sha(p) == wanted, "local original raw differs")
            cc.require(value["output_valid"] is True and value["arm"] == "R" and value["window"] == part["window"] and
                value["context_audit"]["context_source_sha256"] == job["source_key"] and
                value["context_audit"]["deliberately_wrong_context_diagnostic_only"] is False,
                "wrong or failed context cannot enter production")
            accepted = dict(value, start_sec=part["start_sec"], end_sec=part["end_sec"], index=ix,
                clock_record_sha256=part["clock_record_sha256"], clock_branch=part["clock_branch"],
                raw_source_pts_origin_sec=part["raw_source_pts_origin_sec"])
            record["windows"].append(accepted)
        rows.append(record)
    old.write_rows(out / "temporal.jsonl", rows)
    rt.raw_write(out / "temporal.stage.json", dict(status="PASS_TEMPORAL_EXECUTION", videos=len(rows),
        windows=sum(len(x["windows"]) for x in rows), invalid_windows=0, output_sha256=ex.sha(out / "temporal.jsonl"),
        logical_parameters=8782459120, allow_empty=True, all_original_local_windows_run=True,
        overview_sources=len(plan["sources"]), sparse_overview_not_negative_supervision=True,
        selected_adapter_sha256=terminal["model_identity"]["adapter_sha256"], new_optimizer_updates=0))


def finish(scope):
    ex.verify()
    _, old, frames, production = rt.bind_helpers()
    out = rt.HERE / (scope + "_01")
    ref, manifest, clocks = old.inputs(scope)
    # Fail before scheduling rather than silently start a different spatial job.
    cc.require((rt.RUN / "teacher_student_autopilot_v14/cache_01" / (scope + ".json")).is_file(), "exact full spatial cache missing")
    production.scheduling(scope, out)
    space = ex.read(out / "spatial.stage.json")
    cc.require(space["status"] in ("PASS_STRICT_SOURCE_FIELD_SPATIAL", "PASS_EMPTY_SPACE_NO_MODEL_CALL") and
        (space.get("reused_cache") is True or space["status"] == "PASS_EMPTY_SPACE_NO_MODEL_CALL"), "unregistered fresh spatial execution")
    from field_contract import compose_from_field
    from package_contract import package, validate_predictions, keyset
    selected = old.rows(out / "selected.jsonl")
    projected = frames.legacy_manifest(manifest)
    predictions, provenance = compose_from_field(projected, selected, old.rows(out / "field_shots.jsonl"),
        old.rows(out / "anchor_requests.jsonl"), old.rows(out / "anchor_output.jsonl"))
    old.write_rows(out / "predictions.jsonl", predictions)
    old.write_rows(out / "provenance.jsonl", provenance)
    accepted = validate_predictions(projected, predictions, keyset(selected), provenance)
    rt.raw_write(out / "metadata.json", {"records": manifest["records"], "errors": []})
    pending = out / "candidate_C_ADVISORY_8B.PENDING.zip"
    accepted.update(package(out / "predictions.jsonl", pending))
    subprocess.run([sys.executable, "-B", str(rt.RUN / "baseline_a_pts_v1/vendor/independent_validate.py"),
        "--strict-loader-root", str(rt.RUN / "baseline_a_pts_v1/vendor/frozen_strict_loader"),
        "--metadata", str(out / "metadata.json"), "--selected", str(out / "selected.jsonl"),
        "--predictions", str(out / "predictions.jsonl"), "--provenance", str(out / "provenance.jsonl"),
        "--zip", str(pending), "--report", str(out / "independent_validation.json")], check=True)
    independent = ex.read(out / "independent_validation.json")
    production.check_independent(independent, scope, len(selected))
    for name, key in (("predictions.jsonl", "predictions_sha256"), ("provenance.jsonl", "provenance_sha256")):
        cc.require(ex.sha(out / name) == independent[key], "independently accepted output SHA differs")
    cc.require(independent["zip_sha256"] == ex.sha(pending), "independently accepted archive SHA differs")
    with zipfile.ZipFile(pending) as z:
        cc.require(z.namelist() == ["predictions.jsonl"] and z.testzip() is None and
            z.read("predictions.jsonl") == (out / "predictions.jsonl").read_bytes(), "actual ZIP CRC/content failure")
    candidate = out / "candidate_C_ADVISORY_8B.zip"
    cc.require(not candidate.exists(), "final ZIP already exists")
    pending.rename(candidate)
    accepted.update(status="PASS_COMPLETE_C_ADVISORY_8B_PACKAGE_ON_LINUX", candidate=str(candidate), scope=scope,
        actual_zip_bytes=candidate.stat().st_size, actual_zip_sha256=ex.sha(candidate),
        complete_pipeline_parameters=8782459120, shared_base_counted_once=True,
        selected_adapter_sha256="8e2cca463d8aac39f7a709bdf562373e3e47a3a8da490991c303d5e03b803b23",
        new_optimizer_updates=0, new_spatial_model_calls=0, old_spatial_cost_preserved=True,
        official_score=None, uploaded=False, automatic_return=False, source_lock_sha256=ex.sha(rt.HERE / "source_lock.json"))
    rt.raw_write(out / "package.stage.json", accepted)
    print(json.dumps(accepted), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("stage", choices=("assemble", "finish")); p.add_argument("scope", choices=("nontest", "rematch"))
    args = p.parse_args(); globals()[args.stage](args.scope)
