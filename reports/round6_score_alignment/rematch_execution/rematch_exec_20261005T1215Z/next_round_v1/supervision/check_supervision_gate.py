"""CPU-only first-workday stop decision. A data pass does not authorize training."""
import argparse
import datetime as dt
import json
import math
from pathlib import Path

from select_windows import HERE, require

FIRST_WORKDAY_END = "2026-10-07T23:59:59+08:00"
REVIEW_FLAGS = ("input_coverage_and_event_explanations_reviewed", "source_group_isolation_pass",
    "no_unknown_or_unobserved_gaps_certified_negative", "no_forced_empty_quota",
    "teacher_long_interval_and_all_positive_bias_reviewed", "boundary_and_multisegment_behavior_reviewed")


def decision(teacher_capacity, validation, review, now):
    deadline = dt.datetime.fromisoformat(FIRST_WORKDAY_END)
    require(isinstance(now, dt.datetime) and now.tzinfo is not None, "timezone-aware gate timestamp required")
    reasons = []
    if not teacher_capacity or teacher_capacity.get("status") != "PASS_REAL_STRONGER_TEACHER_ADMISSION":
        reasons.append("Stronger 32B teacher has no real capacity/runtime admission; same-8B substitution forbidden")
    if not validation:
        reasons.append("New real teacher validation receipt unavailable")
    else:
        for split in ("train", "dev"):
            if validation.get("positive_by_split", {}).get(split, 0) < 1:
                reasons.append(split + " lacks an explainable validated positive window")
            if validation.get("explicit_empty_by_split", {}).get(split, 0) < 1:
                reasons.append(split + " lacks a justified explicit-no-highlight window; do not manufacture one")
        n = validation.get("eligible_by_split", {}).get("train", 0)
        if type(n) is not int or math.ceil(n / 16) * 3 < 20:
            reasons.append("Validated train population cannot yield the requested 20-update pilot within max three epochs")
        if validation.get("unlabelled_windows_never_converted_to_empty") is not True:
            reasons.append("Unlabelled-to-empty exclusion not evidenced")
        if validation.get("weak_teacher_only") is not True:
            reasons.append("Weak evidence was not kept distinct from truth")
    if not review or not all(review.get(flag) is True for flag in REVIEW_FLAGS):
        reasons.append("Main-controller semantic explanation/coverage/bias review incomplete")
    if reasons:
        status = "STOP_T_FIRST_WORKDAY_SUPERVISION_UNAVAILABLE" if now >= deadline else "T_NOT_ADMITTED_PREPARATION_ONLY"
    else:
        status = "PASS_SUPERVISION_PREPARATION_ONLY_REQUIRES_TRAINING_ADMISSION"
    return {"schema": "aic_complete_window_first_workday_gate_v1", "checked_utc": now.astimezone(dt.timezone.utc).isoformat(),
        "status": status, "reasons": reasons, "first_workday_end": FIRST_WORKDAY_END,
        "semantic_training_admitted": False, "gpu_job_started": False,
        "continue_low_cost_candidate": "Z_WITHOUT_WAITING_FOR_T", "M_status": "ALREADY_DELIVERED",
        "same_8b_teacher_fallback": False, "forced_empty_quota": False,
        "current_teacher_capacity_status": teacher_capacity.get("status") if teacher_capacity else None}


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--teacher-admission", type=Path, required=True)
    parser.add_argument("--validation-receipt", type=Path)
    parser.add_argument("--semantic-review", type=Path)
    parser.add_argument("--output", type=Path, required=True)
    args = parser.parse_args()
    read = lambda path: json.loads(path.read_text(encoding="utf-8")) if path and path.is_file() else None
    teacher = read(args.teacher_admission)
    teacher = teacher.get("capacity", teacher) if teacher else None
    result = decision(teacher, read(args.validation_receipt), read(args.semantic_review), dt.datetime.now(dt.timezone.utc))
    output = args.output.resolve()
    require(HERE in output.parents and not output.exists(), "fresh gate output must stay in supervision")
    output.parent.mkdir(parents=True, exist_ok=True)
    output.write_text(json.dumps(result, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")
    print(json.dumps(result, ensure_ascii=False))


if __name__ == "__main__":
    main()
