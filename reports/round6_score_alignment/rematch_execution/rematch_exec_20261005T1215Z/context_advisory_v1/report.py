"""Label-blind mechanism reports, then fixed full-reference investment rule."""
import argparse
from collections import defaultdict
import json
from pathlib import Path
import statistics
import context_contract as cc
import runtime as rt
import experiment as ex


def records(stage):
    if stage == "nontest":
        plan = ex.read(rt.HERE / "input_01/nontest_plan.json")
        jobs = plan["jobs"]
        out = rt.HERE / "nontest_01"
    else:
        plan = ex.read(rt.HERE / "input_01/developer_plan.json")
        jobs = plan["developer_jobs"]
        if stage == "pilot":
            jobs = [x for x in jobs if x["video_id"] in plan["pilot_video_ids"]]
        out = rt.HERE / "developer_01"
    arms = ("B1", "B0", "N", "R", "X") if stage != "full" else ("B0", "N", "R", "X")
    answer = []
    from contracts import parse_segments
    from native_segment_contract import native_segment_ranges
    sources = ex.source_tables(plan)
    for job in jobs:
        entry = {"video_id": job["video_id"], "source_group": job["source_group"], "arms": {}}
        for arm in arms:
            intervals, native_ids, tokens, count = [], set(), 0, 0
            generated_seconds, local_diagnostics = 0.0, []
            for ix, part in enumerate(job["windows"]):
                folder = out / "local" / cc.digest(job["video_id"]) / str(ix) / arm
                value = ex.read(folder / "done.json")
                cc.require(value["output_valid"] and value["arm"] == arm, "incomplete diagnostic arm")
                for p, wanted in value["bound_files"].items():
                    cc.require(ex.sha(p) == wanted, "diagnostic raw changed")
                w = part["window"]
                parsed, errors, _ = parse_segments(value["raw_output"], w["window_duration_sec"], allow_empty=arm != "B1")
                cc.require(not errors and parsed == value["parsed_segments"], "diagnostic validator mismatch")
                native = native_segment_ranges(parsed, value["video_identity"]["window_source_pts_sec"],
                    w["window_pts_start_sec"], w["window_duration_sec"])
                cc.require([list(x) for x in native] == value["native_frame_realizability"]["ranges"], "native selection receipt changed")
                base = w["planned_source_frame_ordinals"][0]
                for a, b in native:
                    native_ids.update(range(base + a, base + b))
                offset = part["start_sec"] - job.get("clip_start_sec", 0)
                intervals += [[offset + a, offset + b] for a, b in parsed]
                tokens += value["input_tokens"]; count += 1
                generated_seconds += value["generation_seconds"]
                gaps = [b-a for a,b in zip(value["window"]["planned_actual_pts_sec"], value["window"]["planned_actual_pts_sec"][1:])]
                local_diagnostics.append({"window_duration_seconds": w["window_duration_sec"],
                    "legal_empty": not parsed, "segments_shorter_than_2_seconds": sum(b-a < 2 for a,b in parsed),
                    "endpoint_touching_segments": sum(a == 0 or b == w["window_duration_sec"] for a,b in parsed),
                    "selected_fraction": cc.seconds(parsed) / w["window_duration_sec"],
                    "median_actual_sample_gap_seconds": statistics.median(gaps) if gaps else None,
                    "maximum_actual_sample_gap_seconds": max(gaps) if gaps else None,
                    "output_tokens": value["output_tokens"]})
            own = {"segments": intervals, "native_source_ordinals": sorted(native_ids), "input_tokens": tokens,
                "local_calls": count, "selected_seconds": cc.seconds(intervals), "legal_empty": not intervals,
                "model_generation_seconds": generated_seconds, "local_diagnostics": local_diagnostics}
            if stage == "full":
                own["closed_world_teacher_set_agreement"] = cc.weak_metrics(intervals, job["weak_reference"])
            entry["arms"][arm] = own
        entry["native_selected_sets_R_N_equal"] = entry["arms"]["R"]["native_source_ordinals"] == entry["arms"]["N"]["native_source_ordinals"]
        entry["native_selected_sets_R_X_equal"] = entry["arms"]["R"]["native_source_ordinals"] == entry["arms"]["X"]["native_source_ordinals"]
        answer.append(entry)
    return plan, out, answer


def investment_decision(identical, all_b0_delta, group_down_fraction, four_directions):
    material_negative = all_b0_delta <= -.05 and group_down_fraction >= .75
    direction = all(x >= 0 for x in four_directions)
    return (not identical and not material_negative and direction), material_negative, direction


def bootstrap_video_macro(values, rows, draws=10000):
    import numpy as np
    keys = sorted(set(x["source_group"] for x in rows))
    sums, counts = [], []
    for key in keys:
        xs = [v for v, r in zip(values, rows) if r["source_group"] == key]
        sums.append(sum(xs)); counts.append(len(xs))
    rng = np.random.default_rng(20261009)
    sums, counts = np.array(sums), np.array(counts)
    sampled = rng.integers(0, len(keys), (draws, len(keys)))
    replicas = sums[sampled].sum(1) / counts[sampled].sum(1)
    return {"mean": statistics.mean(values), "ci95": np.quantile(replicas, [.025, .975]).tolist(),
        "resampling_units": len(keys), "point_estimator": "VIDEO_MACRO_RECOMPUTED_AFTER_SOURCE_GROUP_RESAMPLE",
        "draws": draws, "seed": 20261009, "CI_is_report_only": True}


def execute(stage):
    ex.verify()
    rt.bind_helpers()
    plan, out, items = records(stage)
    if stage != "full":
        result = {"status": "PASS_LABEL_BLIND_MECHANISM_REPORT_NOT_QUALITY", "records": len(items),
            "source_groups": len({r["source_group"] for r in items}),
            "R_N_changed_native_sets": sum(not r["native_selected_sets_R_N_equal"] for r in items),
            "R_X_changed_native_sets": sum(not r["native_selected_sets_R_X_equal"] for r in items),
            "weak_reference_used": False, "hallucination_rate": "UNKNOWN_NO_INDEPENDENT_SEMANTIC_REFERENCE",
            "not_a_highlight_quality_or_official_score": True, "next": "FIXED_FULL_104_FOUR_ARMS" if stage == "pilot" else "FIXED_PILOT_24_FIVE_ARMS"}
    else:
        cc.require(len(items) == 104 and len({r["source_group"] for r in items}) == 96, "104/96 report denominator changed")
        pilot_groups = set(plan["pilot_source_groups"])
        untouched = [r for r in items if r["source_group"] not in pilot_groups]
        cc.require(len({r["source_group"] for r in untouched}) == 72, "new72 group report denominator")
        f1 = lambda r, arm: r["arms"][arm]["closed_world_teacher_set_agreement"]["f1"]
        comparisons = {}
        for subset_name, subset in (("all104", items), ("new72_source_groups", untouched)):
            comparisons[subset_name] = {"records": len(subset), "source_groups": len({r["source_group"] for r in subset})}
            for control in ("B0", "N", "X"):
                comparisons[subset_name]["R_minus_" + control] = bootstrap_video_macro([f1(r, "R") - f1(r, control) for r in subset], subset)
        groups = sorted({r["source_group"] for r in items})
        group_down = [statistics.mean(f1(r, "R") - f1(r, "B0") for r in items if r["source_group"] == g) < 0 for g in groups]
        identical = all(r["native_selected_sets_R_N_equal"] for r in items)
        go, material_negative, direction = investment_decision(identical,
            comparisons["all104"]["R_minus_B0"]["mean"], sum(group_down) / len(groups),
            [comparisons[k]["R_minus_" + c]["mean"] for k in comparisons for c in ("B0", "N")])
        result = {"status": "GO_ONE_FROZEN_C_EXPLORATION_PACKAGE" if go else "STOP_C_PRODUCTION_INVESTMENT",
            "records": 104, "source_groups": 96, "comparisons": comparisons,
            "R_N_all_native_selected_sets_identical": identical, "material_negative_investment_rule": material_negative,
            "nonnegative_registered_four_direction_rule": direction, "source_groups_down_vs_B0": sum(group_down),
            "reference_coverage_contract_complete": "UNKNOWN",
            "metric_is_closed_world_external_teacher_output_set_agreement": True,
            "administrative_investment_ranking_not_engineering_or_quality_truth": True,
            "independent_hallucination_or_highlight_quality": "UNKNOWN", "official_score": None,
            "no_prompt_or_threshold_retuning": True, "next": "NONTEST11_STRICT_THEN_426_R_ONLY" if go else "EXACT_NONTEST_S_REFERENCE_INVENTORY_THEN_B_DIAGNOSTIC"}
    result["arm_diagnostics"] = {arm: {
        "records": len(items), "legal_empty_records": sum(r["arms"][arm]["legal_empty"] for r in items),
        "local_windows": sum(r["arms"][arm]["local_calls"] for r in items),
        "local_input_tokens": sum(r["arms"][arm]["input_tokens"] for r in items),
        "model_generation_seconds": sum(r["arms"][arm]["model_generation_seconds"] for r in items),
        "short_segments_under_2s": sum(d["segments_shorter_than_2_seconds"] for r in items for d in r["arms"][arm]["local_diagnostics"]),
        "endpoint_touching_segments": sum(d["endpoint_touching_segments"] for r in items for d in r["arms"][arm]["local_diagnostics"]),
        "near_complete_windows_fraction_ge_099": sum(d["selected_fraction"] >= .99 for r in items for d in r["arms"][arm]["local_diagnostics"]),
        "generation_seconds_are_not_total_GPU_charge": True} for arm in items[0]["arms"]}
    rt.raw_write(out / (stage + ".mechanism_rows.json"), items)
    rt.raw_write(out / (stage + ".report.json"), result)
    print(json.dumps(result), flush=True)


if __name__ == "__main__":
    p = argparse.ArgumentParser(); p.add_argument("stage", choices=("nontest", "pilot", "full"))
    execute(p.parse_args().stage)
