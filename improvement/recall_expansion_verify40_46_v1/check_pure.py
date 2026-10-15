"""Bounded synthetic checks for exact plans, byte preservation and KEEP-only merge."""
from copy import deepcopy
from fractions import Fraction
import json
from pathlib import Path
import subprocess
import sys
from tempfile import TemporaryDirectory

sys.dont_write_bytecode = True

from overlap_plan import SOURCE_SCHEMA, plan_baseline_sources, plan_overlapping_sources
from merge_keep import CANDIDATE_SCHEMA, baseline_records, merge_verified_candidates
from overlap_plan import validate_sources


def source(video_id="landscape", end="32", ratio=(16, 9), rate=8):
    span = Fraction(end)
    count = int(span * rate)
    return dict(video_id=video_id, source_sha256=("a" if video_id == "landscape" else "b") * 64,
        width=160 if ratio == (16, 9) else 90, height=90 if ratio == (16, 9) else 160,
        n_frames=count, targetRatioWH=list(ratio), normalized_exact_pts=[str(Fraction(i, rate)) for i in range(count)],
        physical_end_exact=str(span))


def document(*sources):
    return dict(schema=SOURCE_SCHEMA, sources=list(sources))


def rejected(call):
    try:
        call()
    except (ValueError, UnicodeError):
        return
    raise AssertionError("Invalid input was accepted")


def candidate(candidate_id, first, last, decision="KEEP", **extra):
    return dict(candidate_id=candidate_id, video_id="landscape", source_sha256="a" * 64,
        start_exact=first, end_exact=last, decision=decision, execution_status="MODEL_OK",
        independent_cpu_qa_status="PASS", **extra)


def check_plans():
    values = document(source())
    overlap = plan_overlapping_sources(values)
    assert [(w["start_exact"], w["end_exact"]) for w in overlap["sources"][0]["windows"]] == [
        ("0", "15"), ("15/2", "45/2"), ("15", "30"), ("17", "32")]
    baseline = plan_baseline_sources(values)
    assert [(w["start_exact"], w["end_exact"]) for w in baseline["sources"][0]["windows"]] == [("0", "16"), ("16", "32")]
    for plan in (overlap, baseline):
        for window in plan["sources"][0]["windows"]:
            first, stop = window["eligible_first"], window["eligible_stop"]
            expected = [first + j * (stop - first - 1) // 63 for j in range(64)]
            assert window["source_frame_ordinals"] == expected and len(set(expected)) == 64
            assert expected[0] == first and expected[-1] == stop - 1
    exact_tail = plan_overlapping_sources(document(source(end="30")))
    assert exact_tail["window_count"] == 3  # The right-aligned final window is not duplicated.
    fractional = plan_overlapping_sources(document(source(end="249/8")))
    assert fractional["sources"][0]["windows"][-1]["end_exact"] == "249/8"
    short_doc = document(source(end="12"))
    short_overlap, short_baseline = plan_overlapping_sources(short_doc), plan_baseline_sources(short_doc)
    assert short_overlap["window_count"] == short_baseline["window_count"] == 1
    assert short_overlap["sources"][0]["windows"][0]["input_view_key"] == short_baseline["sources"][0]["windows"][0]["input_view_key"]
    assert short_overlap["baseline_shared_view_count"] == short_overlap["combined_unique_view_budget"] == 1
    assert short_overlap["overlap_B0_new_model_call_budget"] == 0
    rejected(lambda: plan_overlapping_sources(document(source(end="3"))))
    rejected(lambda: plan_baseline_sources(document(source(end="3"))))
    invalid = deepcopy(values)
    invalid["sources"][0]["normalized_exact_pts"][1] = "0"
    rejected(lambda: plan_overlapping_sources(invalid))
    invalid = deepcopy(values)
    invalid["sources"][0]["physical_end_exact"] = 32.0
    rejected(lambda: plan_baseline_sources(invalid))
    rejected(lambda: plan_baseline_sources(document(source(), source())))
    return "exact_baseline_overlap_plans_and_shared_view_budget"


BASELINE = (b'{ "video_id":"landscape", "targetRatioWH": [ 16, 9 ], "predictions": '
    b'[ { "frame":1, "bboxes": [ 0.000, 0, 160.0 ] }, {"frame":10,"bboxes":[0,0,1.6e2]} ] }\r\n'
    b'{"video_id":"portrait","targetRatioWH":[9,16],"predictions":[{"frame":3,"bboxes":[0.0,0,90]}]}')


def check_merge():
    values = document(source(), source("portrait", ratio=(9, 16)))
    calls = []
    def field(video_id, frame):
        calls.append((video_id, frame))
        return dict(status="ACCEPTED_SOURCE_FIELD_FRAME", video_id=video_id, frame=frame,
            source_sha256="a" * 64, targetRatioWH=[16, 9], bboxes=[0, 0, 160.0])
    candidates = dict(schema=CANDIDATE_SCHEMA, candidates=[candidate("keep1", "1", "3/2"),
        candidate("keep2", "9/8", "13/8"), candidate("unknown", "2", "3", "UNKNOWN"),
        candidate("drop", "3", "4", "DROP")])
    merged = merge_verified_candidates(values, BASELINE, candidates, field)
    assert calls == [("landscape", i) for i in (8, 9, 11, 12)]
    assert merged.gate["added_frames"] == 4 and merged.gate["UNKNOWN_or_DROP_new_frames"] == 0
    assert merged.gate["nonzero_prediction_difference"] and not merged.gate["scientific_quality_pass"]
    before = baseline_records(BASELINE, validate_sources(values))
    after = baseline_records(merged.predictions_jsonl, validate_sources(values))
    for old, new in zip(before, after):
        assert old["ratio_bytes"] == new["ratio_bytes"]
        assert all(new["raw_by_frame"][key] == raw for key, raw in old["raw_by_frame"].items())
    assert merged.predictions_jsonl.endswith(BASELINE.split(b"\r\n")[1])
    zero = merge_verified_candidates(values, BASELINE,
        dict(schema=CANDIDATE_SCHEMA, candidates=[candidate("same", "5/4", "11/8")]), field)
    assert zero.predictions_jsonl == BASELINE and zero.gate["status"] == "FAIL_ZERO_PREDICTION_DIFFERENCE"
    assert not zero.gate["candidate_ready_for_quality_gate"] and not zero.gate["deliverable_claimed"]
    for key, bad in (("execution_status", "INFERENCE_FAILURE"), ("independent_cpu_qa_status", "FAILED"),
                     ("decision", None), ("source_sha256", "b" * 64), ("start_exact", "3/2"),
                     ("end_exact", "33"), ("start_exact", 1.0)):
        item = candidate("invalid", "1", "3/2")
        item[key] = bad
        rejected(lambda item=item: merge_verified_candidates(values, BASELINE,
            dict(schema=CANDIDATE_SCHEMA, candidates=[item]), field))
    duplicate = dict(schema=CANDIDATE_SCHEMA, candidates=[candidate("same", "1", "3/2")] * 2)
    rejected(lambda: merge_verified_candidates(values, BASELINE, duplicate, field))
    rejected(lambda: merge_verified_candidates(values, BASELINE.replace(b'"frame":10', b'"frame":1'), candidates, field))
    rejected(lambda: merge_verified_candidates(document(source()), BASELINE, candidates, field))
    rejected(lambda: merge_verified_candidates(values, BASELINE, candidates,
        lambda v, f: dict(status="UNKNOWN", video_id=v, frame=f)))
    rejected(lambda: merge_verified_candidates(values, BASELINE, candidates,
        lambda v, f: dict(status="ACCEPTED_SOURCE_FIELD_FRAME", video_id=v, frame=f,
            source_sha256="a" * 64, targetRatioWH=[16, 9], bboxes=[0, 0, 161])))
    return "KEEP_only_merge_byte_preservation_and_failure_rejection"


def check_cli():
    here = Path(__file__).resolve().parent
    with TemporaryDirectory(prefix="recall_pure_") as temporary:
        root = Path(temporary)
        values = document(source(), source("portrait", ratio=(9, 16)))
        (root / "sources.json").write_text(json.dumps(values), encoding="utf-8")
        (root / "baseline.jsonl").write_bytes(BASELINE)
        (root / "candidates.json").write_text(json.dumps(dict(schema=CANDIDATE_SCHEMA,
            candidates=[candidate("new", "1", "3/2")])), encoding="utf-8")
        rows = [dict(status="ACCEPTED_SOURCE_FIELD_FRAME", video_id="landscape", frame=frame,
            source_sha256="a" * 64, targetRatioWH=[16, 9], bboxes=[0, 0, 160]) for frame in (8, 9, 11)]
        (root / "field.jsonl").write_text("\n".join(map(json.dumps, rows)), encoding="utf-8")
        for mode in ("baseline", "overlap"):
            result = subprocess.run([sys.executable, "-B", str(here / "overlap_plan.py"), "--mode", mode,
                "--sources", str(root / "sources.json"), "--output", str(root / (mode + ".json"))],
                capture_output=True, text=True)
            assert result.returncode == 0, result.stderr
        command = [sys.executable, "-B", str(here / "merge_keep.py")]
        for option, name in (("sources", "sources.json"), ("baseline", "baseline.jsonl"),
                             ("candidates", "candidates.json"), ("accepted-field", "field.jsonl"),
                             ("predictions-output", "merged.jsonl"), ("diff-output", "diff.json"), ("gate-output", "gate.json")):
            command.extend(["--" + option, str(root / name)])
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode == 0, result.stderr
        gate = json.loads((root / "gate.json").read_text())
        assert gate["added_frames"] == 3 and not gate["submission_package_created"]
        result = subprocess.run(command, capture_output=True, text=True)
        assert result.returncode != 0  # Successful output cannot be overwritten.
    return "CLI_outputs_and_existing_output_refusal"


if __name__ == "__main__":
    groups = [check_plans(), check_merge(), check_cli()]
    print(json.dumps(dict(status="PASS_PURE_SYNTHETIC_CHECKS_NOT_QUALITY", groups=groups,
        media_decodes=0, model_calls=0, GPU_admitted=False, scientific_quality_pass=False)))
