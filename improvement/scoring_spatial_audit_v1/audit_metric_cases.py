"""Read-only hand cases for the published joint metric, never contest data.

This module imports only the existing internal scorer and evaluates synthetic
geometry/counts. It neither reads predictions nor measures model quality.
"""
from __future__ import annotations

import json
import math
import sys
from fractions import Fraction as F
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
SCORER = ROOT / "reports/boundary_refinement_20261012_v1/input_01/validator/frozen_strict_loader"
REPORT = ROOT / "reports/scoring_spatial_audit_20261013_v1"


def main():
    target = REPORT / "synthetic_metric_cases_01.json"
    if target.exists():
        raise FileExistsError("Completed audit cases must not be rerun or overwritten")
    sys.path.insert(0, str(SCORER))
    from aic6.scoring import Box, _zero_case, spatial_iou

    checks = []

    def check(name, actual, expected):
        if not math.isclose(actual, float(expected), rel_tol=0, abs_tol=1e-12):
            raise AssertionError((name, actual, expected))
        checks.append(dict(name=name, actual=actual, expected_exact=str(expected)))

    # Exact same frame sets can score poorly because their crop geometry differs.
    original = Box(0, 0, 160, 90)
    inset = Box(20, 11.25, 120, 67.5)
    overlap = spatial_iou(original, inset)
    check("same_ratio_contained_width075_IoU", overlap, F(9, 16))
    check("time_F1_one_perfect_match", _zero_case(1, 1, 1)[2], F(1))
    check("same_frame_wide_crop_joint_F1", _zero_case(1, 1, overlap)[2], F(9, 16))
    check("matching_smaller_reference_joint_F1", _zero_case(1, 1, spatial_iou(inset, inset))[2], F(1))
    check("shrink_hurts_when_reference_is_full", _zero_case(1, 1, spatial_iou(inset, original))[2], F(9, 16))

    # A newly selected genuine positive frame may STILL lower joint F1.
    # Baseline matches two of three GT frames at .8 IoU each. The new third
    # frame has .1 IoU: temporal recall improves, but denominator cost dominates.
    old = _zero_case(2, 3, 1.6)[2]
    new = _zero_case(3, 3, 1.7)[2]
    check("expansion_old_joint_F1", old, F(16, 25))
    check("expansion_new_joint_F1", new, F(17, 30))
    check("expansion_old_temporal_F1", _zero_case(2, 3, 2)[2], F(4, 5))
    check("expansion_new_temporal_F1", _zero_case(3, 3, 3)[2], F(1))
    assert new < old

    # Native VFR: labels and predictions remain unchanged. Duration-weighting
    # and counting source frames are different evaluation tasks.
    check("VFR_frame_count_F1", _zero_case(1, 3, 1)[2], F(1, 2))
    vfr_duration_f1 = F(2) * F(7, 10) / (F(7, 10) + F(9, 10))
    check("VFR_duration_proxy_F1", float(vfr_duration_f1), F(7, 8))
    check("empty_both", _zero_case(0, 0, 0)[2], F(1))
    check("one_side_empty", _zero_case(1, 0, 0)[2], F(0))
    check("duplicate_prediction_denominator", _zero_case(2, 1, 1)[2], F(2, 3))

    # Per-video averaging cannot be replaced with pooled frame averaging.
    macro = (_zero_case(1, 1, .2)[2] + _zero_case(100, 100, 100)[2]) / 2
    micro = _zero_case(101, 101, 100.2)[2]
    check("macro_video_average", macro, F(3, 5))
    check("pooled_frames_differ", micro, F(501, 505))

    result = dict(
        status="PASS_SYNTHETIC_PUBLISHED_FORMULA_CASES_NOT_OFFICIAL_EVALUATOR",
        checks=checks, cases=len(checks),
        formula="F_i=2*S_i/(P_i+G_i); Score=100*mean_i(F_i)",
        expansion_condition="adding k frames helps iff delta_S/k > S_i/(P_i+G_i)=F_i/2",
        expansion_condition_requires_unknown_per_video_reference=True,
        use_leaderboard_macro_as_per_video_threshold=False,
        fixed_selected_frame_set="crop-only improvement is proportional to change in matched-frame IoU sum",
        references="synthetic only", contest_media_read=False, contest_GT_read=False,
        real_model_calls=0, native_decodes=0, optimizer_updates=0,
        candidate_evaluation=False, package_admitted=False,
    )
    REPORT.mkdir(parents=True, exist_ok=True)
    with target.open("x", encoding="utf-8") as stream:
        json.dump(result, stream, ensure_ascii=False, indent=2, allow_nan=False)
        stream.write("\n")
    print(json.dumps({"status": result["status"], "hand_checks": len(checks), "new_model_calls": 0}))


if __name__ == "__main__":
    main()
