"""One authorized asset inventory and an exact B-boundary handoff, not training."""
import argparse
import hashlib
from pathlib import Path
import context_contract as cc
import runtime as rt
import experiment as ex


def inventory():
    ex.verify()
    plan = ex.read(rt.HERE / "input_01/developer_plan.json")
    non = ex.read(rt.HERE / "input_01/nontest_plan.json")
    # Only registered independent composition references can support S. Model
    # boxes, including the preserved B2 spatial field, are not such references.
    authority_path = rt.HERE / "s_reference_authority.json"
    cc.require(not authority_path.exists(), "unregistered S authority injected after freeze")
    rt.raw_write(rt.HERE / "fallback_s_inventory.json", {
        "status": "EVIDENCE_INSUFFICIENT_NO_REGISTERED_INDEPENDENT_COMPOSITION_REFERENCE",
        "registered_nontest_records": len(non["jobs"]), "developer_records": len(plan["developer_jobs"]),
        "developer_groups": len({j["source_group"] for j in plan["developer_jobs"]}),
        "independent_composition_reference_frames": 0,
        "coverage_of_other_unregistered_assets": "UNKNOWN_NOT_SCANNED",
        "model_or_detector_boxes_are_not_composition_truth": True,
        "new_spatial_model_calls": 0, "new_model_downloads": 0})
    rt.bind_helpers()
    from contracts import parse_segments
    sources = ex.source_tables(plan)
    seeds = []
    for job in plan["developer_jobs"]:
        for ix, part in enumerate(job["windows"]):
            p = rt.HERE / "developer_01/local" / cc.digest(job["video_id"]) / str(ix) / "B0/done.json"
            value = ex.read(p)
            for name, wanted in value["bound_files"].items():
                cc.require(ex.sha(name) == wanted, "B-boundary seed raw changed")
            parsed, errors, _ = parse_segments(value["raw_output"], part["window"]["window_duration_sec"], allow_empty=True)
            cc.require(not errors and parsed == value["parsed_segments"], "B-boundary seed validator mismatch")
            sampled = part["window"]["planned_actual_pts_sec"]
            gaps = [b-a for a,b in zip(sampled, sampled[1:])]
            if not gaps:
                continue
            shift = sorted(gaps)[len(gaps)//2]
            for event_index, (a,b) in enumerate(parsed):
                absolute = [part["start_sec"]+a, part["start_sec"]+b]
                start, end = part["start_sec"], part["end_sec"]
                duration = sources[job["source_key"]]["raw_end_exclusive_sec"]
                shifted = [[start+s, end+s] for s in (-shift, shift)
                    if start+s >= 0 and end+s <= duration and start+s <= absolute[0] and absolute[1] <= end+s]
                if not shifted:
                    continue
                key = cc.digest([job["video_id"], ix, event_index])
                seeds.append({"event_key": key, "video_id": job["video_id"], "source_group": job["source_group"],
                    "source_key": job["source_key"], "source_path": sources[job["source_key"]]["source_path"],
                    "raw_source_event_seconds": absolute, "original_window": part["window"],
                    "shifted_context_source_seconds": shifted, "original_B0_done": str(p), "original_B0_done_sha256": ex.sha(p),
                    "candidate_outside_unknown_not_negative": True,
                    "independent_boundary_direction": "UNKNOWN_REQUIRES_SEPARATE_EVIDENCE"})
    chosen, seen = [], set()
    for seed in sorted(seeds, key=lambda x: x["event_key"]):
        if seed["source_group"] not in seen:
            chosen.append(seed); seen.add(seed["source_group"])
        if len(chosen) == 16:
            break
    result = {"status": "CPU_REGISTERED_B_EVENT_SHIFT_DIAGNOSTIC_HANDOFF_NOT_GPU_OR_TRAINING",
        "events": chosen, "denominator": len(chosen), "requested_events": 16,
        "selection": "FIRST_SHA_EVENT_PER_SOURCE_GROUP_NO_WEAK_SCORE_SELECTION",
        "reference_coverage_complete": "UNKNOWN", "stability_is_not_boundary_truth": True,
        "new_32B_calls": 0, "optimizer_updates": 0,
        "next_agent_action": "IMPLEMENT_AND_FREEZE_MATCHED_ORIGINAL_AND_SHIFTED_32B_BOUNDARY_DIAGNOSTIC_WITH_RAW_BEFORE_VALIDATION",
        "training_requires_independent_direction_evidence": True, "user_confirmation_required": False}
    rt.raw_write(rt.HERE / "fallback_b_diagnostic_handoff.json", result)
    print(result["status"], result["denominator"], flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("stage", choices=("inventory",)); p.parse_args()
    inventory()
