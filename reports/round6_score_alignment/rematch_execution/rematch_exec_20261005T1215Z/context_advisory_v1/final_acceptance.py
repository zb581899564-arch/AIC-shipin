"""Independent CPU closure of real outputs, raw answers, ZIP and ledger."""
import json
import math
from pathlib import Path
import subprocess
import sys
import zipfile
import context_contract as cc
import runtime as rt
import experiment as ex


def main():
    ex.verify()
    _, old, frames, production = rt.bind_helpers()
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    reports = {}
    for scope, denominator, expected_windows in (("nontest", 8, 8), ("rematch", 426, 521)):
        out = rt.HERE / (scope + "_01")
        ref, manifest, clocks = old.inputs(scope)
        plan = ex.read(rt.HERE / "input_01" / (scope + "_plan.json"))
        temporal = old.rows(out / "temporal.jsonl")
        cc.require(len(temporal) == denominator and len(plan["jobs"]) == denominator and
            {x["video_id"] for x in temporal} == {x["video_id"] for x in manifest["records"]}, "final identity denominator")
        cc.require(sum(len(x["windows"]) for x in temporal) == expected_windows, "final natural window denominator")
        window_count = 0
        for job in plan["jobs"]:
            table = ex.read(out / "overview" / job["source_key"] / "done.json")
            w = ex.overview_window(plan["sources"][job["source_key"]], job["source_key"])
            req = {"kind": "overview", "window": w, "prompt": rt.OVERVIEW_TEXT, "model": table["model_identity"],
                "max_input": 16384, "max_output": 1280, "adapter_disabled": True}
            ex.checked_done(out / "overview" / job["source_key"] / "done.json", req)
            raw = ex.read(table["raw_receipt"])
            cc.require(raw["raw_output"] == table["raw_output"] and raw["overview_adapter_disabled"] is True and
                all(isinstance(x, (float, int)) and math.isfinite(x) for x in raw["selected_token_scores"]), "overview raw/scores not accepted")
            cc.validate_overview(raw["raw_output"], w["planned_actual_pts_sec"])
            record = next(x for x in temporal if x["video_id"] == job["video_id"])
            for ix, part in enumerate(job["windows"]):
                p = out / "local" / cc.digest(job["video_id"]) / str(ix) / "R/done.json"
                value = ex.read(p)
                text, audit = ex.arm_text("R", part["window"], table, table, ex.base_texts(old))
                request = {"kind": "local", "window": part["window"], "arm": "R", "prompt": text, "model": value["model_identity"],
                    "max_input": 16384, "max_output": 256, "allow_empty": True, "context_audit": audit}
                ex.checked_done(p, request)
                raw = ex.read(value["raw_receipt"])
                cc.require(raw["raw_output"] == value["raw_output"] and raw["overview_adapter_disabled"] is False and
                    all(isinstance(x, (float, int)) and math.isfinite(x) for x in raw["selected_token_scores"]), "local raw/scores changed")
                parsed, errors, _ = parse_segments(raw["raw_output"], part["window"]["window_duration_sec"], allow_empty=True)
                cc.require(not errors and parsed == value["parsed_segments"] == record["windows"][ix]["parsed_segments"], "final raw temporal validator mismatch")
                native_segment_ranges(parsed, value["video_identity"]["window_source_pts_sec"],
                    part["window"]["window_pts_start_sec"], part["window"]["window_duration_sec"])
                cc.require(value["model_identity"]["adapter_saved_tensor_equality"] == 288 and
                    value["model_identity"]["logical_parameters"] == 8782459120, "final actual model identity")
                window_count += 1
        independent_path = out / "final_independent_validation.json"
        subprocess.run([sys.executable, "-B", str(rt.RUN / "baseline_a_pts_v1/vendor/independent_validate.py"),
            "--strict-loader-root", str(rt.RUN / "baseline_a_pts_v1/vendor/frozen_strict_loader"),
            "--metadata", str(out / "metadata.json"), "--selected", str(out / "selected.jsonl"),
            "--predictions", str(out / "predictions.jsonl"), "--provenance", str(out / "provenance.jsonl"),
            "--zip", str(out / "candidate_C_ADVISORY_8B.zip"), "--report", str(independent_path)], check=True)
        selected = old.rows(out / "selected.jsonl")
        accepted = ex.read(independent_path)
        production.check_independent(accepted, scope, len(selected))
        candidate = out / "candidate_C_ADVISORY_8B.zip"
        cc.require(accepted["zip_sha256"] == ex.sha(candidate) and accepted["predictions_sha256"] == ex.sha(out / "predictions.jsonl"), "final real byte SHA")
        with zipfile.ZipFile(candidate) as archive:
            cc.require(archive.namelist() == ["predictions.jsonl"] and archive.testzip() is None and
                archive.read("predictions.jsonl") == (out / "predictions.jsonl").read_bytes(), "final actual ZIP CRC/single file/original bytes")
        reports[scope] = {"records": denominator, "windows": window_count, "overview_source_files": len(plan["sources"]),
            "independent_sha256": ex.sha(independent_path), "all_11_checks": accepted["checks"],
            "zip_bytes": candidate.stat().st_size, "zip_sha256": ex.sha(candidate), "candidate": str(candidate)}
    ledger_path = Path("/home/inspur/aic_video_work/improvement_round1/gpu_ledger.jsonl")
    ledger = old.rows(ledger_path)
    resources = {}
    for name in ("nontest", "pilot", "full", "rematch"):
        runname = "aic_CAD_v1_" + name
        rows = [x for x in ledger if x["name"] == runname]
        path = rt.RUN / "controller" / (runname + ".resource.json")
        value = ex.read(path)
        cc.require(len(rows) == 1 and rows[0] == value and value["status"] == "completed" and
            value["exit_code"] == 0 and value["stop_reason"] is None and value["charged_seconds"] > 0,
            "final GPU accounting identity/unique terminal")
        resources[name] = {"path": str(path), "sha256": ex.sha(path), "charged_seconds": value["charged_seconds"]}
    result = {"status": "PASS_INDEPENDENT_C_ADVISORY_FINAL", "candidate": reports["rematch"]["candidate"],
        "zip_bytes": reports["rematch"]["zip_bytes"], "zip_sha256": reports["rematch"]["zip_sha256"],
        "reports": reports, "resource_receipts": resources, "ledger_sha256": ex.sha(ledger_path),
        "ledger_historical_offset": 7200, "new_cpu_acceptance_model_calls": 0, "new_optimizer_updates": 0,
        "production_local_weight": "ORIGINAL_B_8B_ADAPTER", "overview_adapter": False,
        "official_score": None, "not_guaranteed_to_exceed_37_63": True,
        "source_lock_sha256": ex.sha(rt.HERE / "source_lock.json")}
    rt.raw_write(rt.HERE / "final_acceptance.json", result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    main()
