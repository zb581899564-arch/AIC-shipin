import pytest
import json
import sys
import hashlib

from diagnose_r7 import main as diagnose_main
from r7_core import (audit_pts_sequence, decide_gate, proportional_targets,
                     select_stratified_groups, temporal_stats, validate_segments)
from temporal_common import parse_segments
from verify_frozen_inputs import main as verify_frozen_inputs_main


def row(group, i, status="usable", duration=8.0, segments=1):
    return {"youtube_id": group, "row_index": i, "mapping_status": status,
            "clip_duration_sec": duration, "n_segments": segments}


def test_pts_cfr_and_nonzero_start_pass():
    pts = [5.0 + i / 30 for i in range(300)]
    got = audit_pts_sequence(pts, 30.0)
    assert got["passed"] and got["max_index_pts_residual_sec"] < 1e-9


def test_pts_one_frame_residual_passes():
    pts = [i / 30 for i in range(10)]
    pts[-1] += 1 / 30
    assert audit_pts_sequence(pts, 30.0)["passed"]


def test_pts_vfr_drift_fails():
    pts = [i / 30 for i in range(60)]
    pts[-1] += 0.2
    got = audit_pts_sequence(pts, 30.0)
    assert not got["passed"] and "residual" in got["reason"]


def test_pts_reverse_and_duplicate_fail():
    assert not audit_pts_sequence([0, 0.04, 0.03], 25)["passed"]
    assert not audit_pts_sequence([0, 0.04, 0.04], 25)["passed"]


@pytest.mark.parametrize("segments,duration", [
    ([], 10),
    ([[0, 1]] * 6, 10),
    ([[-1, 1]], 10),
    ([[0, 11]], 10),
    ([[2, 4], [3, 5]], 10),
])
def test_invalid_segment_contract(segments, duration):
    assert validate_segments(segments, duration)


def test_segment_end_must_not_exceed_clip():
    assert validate_segments([[0, 1], [1, 10.0006]], 10)


def test_valid_segment_contract():
    assert validate_segments([[0, 1], [1, 10]], 10) == []


def test_proportional_allocation_exact():
    got = proportional_targets({"a": 4, "b": 3, "c": 3}, 7)
    assert sum(got.values()) == 7
    assert all(got[k] <= v for k, v in {"a": 4, "b": 3, "c": 3}.items())


def test_deterministic_source_disjoint_split():
    rows = [row(f"g{i:03d}", i, "time_uncertain" if i % 7 == 0 else "usable",
                8 if i % 3 == 0 else 15 if i % 3 == 1 else 24,
                1 if i % 4 < 2 else 2 if i % 4 == 2 else 3)
            for i in range(240)]
    a = select_stratified_groups(rows, {f"g{i:03d}" for i in range(20)})
    b = select_stratified_groups(rows, {f"g{i:03d}" for i in range(20)})
    assert a["dev"] == b["dev"] and a["confirm"] == b["confirm"]
    assert len(a["dev"]) == len(a["confirm"]) == 96
    assert not a["dev"] & a["confirm"]
    assert not a["dev"] & {f"g{i:03d}" for i in range(20)}


def test_split_fails_when_unseen_groups_insufficient():
    with pytest.raises(RuntimeError):
        select_stratified_groups([row(f"g{i}", i) for i in range(191)], set())


def test_metric_empty_invalid_kept_as_zero_against_truth():
    got = temporal_stats([], [[1, 2]])
    assert got["f1"] == 0 and got["recall"] == 0 and got["zero_overlap"]


def gate_payload():
    return {
        "per_arm": {
            "BASE": {"group_macro_f1": .45, "group_macro_precision": .5,
                     "group_macro_recall": .60, "valid_rate": .95,
                     "zero_overlap_videos": 9},
            "P2T2": {"group_macro_f1": .55, "group_macro_precision": .65,
                      "group_macro_recall": .62, "valid_rate": 1.0,
                      "zero_overlap_videos": 6},
            "R7": {"group_macro_f1": .59, "group_macro_precision": .63,
                    "group_macro_recall": .66, "valid_rate": 1.0,
                    "zero_overlap_videos": 5},
        },
        "paired": {"R7_minus_P2T2": {"mean": .04, "ci95": [.01, .08]}},
        "slice_gates": {"multiple_segments": {"passed": True}},
    }


def test_dev_and_confirm_gates_pass():
    data = gate_payload()
    assert decide_gate(data, "dev")["status"] == "R7_DEV_PASS"
    assert decide_gate(data, "confirm")["status"] == "R7_CONFIRM_PASS"


@pytest.mark.parametrize("mutation", [
    ("paired", "mean", .01),
    ("ci", None, -.01),
    ("recall", None, .59),
    ("precision", None, .61),
    ("valid", None, .99),
    ("zero", None, 7),
    ("slice", None, False),
])
def test_gate_failures(mutation):
    data = gate_payload()
    kind, _, value = mutation
    if kind == "paired": data["paired"]["R7_minus_P2T2"]["mean"] = value
    elif kind == "ci": data["paired"]["R7_minus_P2T2"]["ci95"][0] = value
    elif kind == "recall": data["per_arm"]["R7"]["group_macro_recall"] = value
    elif kind == "precision": data["per_arm"]["R7"]["group_macro_precision"] = value
    elif kind == "valid": data["per_arm"]["R7"]["valid_rate"] = value
    elif kind == "zero": data["per_arm"]["R7"]["zero_overlap_videos"] = value
    elif kind == "slice": data["slice_gates"]["multiple_segments"]["passed"] = value
    assert decide_gate(data, "dev")["status"] == "STOP_KEEP_P2T2"


def test_strict_parser_empty_and_overfive_are_invalid():
    assert parse_segments('{"segments": []}', 10)[0] is None
    six = '{"segments": [[0,1],[1,2],[2,3],[3,4],[4,5],[5,6]]}'
    assert parse_segments(six, 10)[0] is None


def test_diagnostics_keeps_invalid_output_in_denominator(tmp_path, monkeypatch):
    manifest = [
        {"video_id": "v1", "youtube_id": "g1", "mapping_status": "usable",
         "clip_duration_sec": 5.0, "n_segments": 1,
         "segments_clip_local": [[1.0, 2.0]]},
        {"video_id": "v2", "youtube_id": "g2", "mapping_status": "time_uncertain",
         "clip_duration_sec": 5.0, "n_segments": 1,
         "segments_clip_local": [[1.0, 2.0]]},
    ]
    def write(name, rows):
        path = tmp_path / name
        path.write_text("".join(json.dumps(r) + "\n" for r in rows), encoding="utf-8")
        return path
    m = write("manifest.jsonl", manifest)
    arm_paths = {}
    for arm in ("BASE", "P2T2", "R7"):
        arm_paths[arm] = write(f"{arm}.jsonl", [
            {"arm": arm, "video_id": "v1", "output_valid": True,
             "parsed_segments": [[1.0, 2.0]]},
            {"arm": arm, "video_id": "v2", "output_valid": arm != "R7",
             "parsed_segments": ([[1.0, 2.0]] if arm != "R7" else None),
             "parse_errors": ([] if arm != "R7" else ["invalid"])},
        ])
    out = tmp_path / "diag.json"
    monkeypatch.setattr(sys, "argv", ["diagnose_r7.py", "--manifest", str(m),
        "--base", str(arm_paths["BASE"]), "--p2t2", str(arm_paths["P2T2"]),
        "--r7", str(arm_paths["R7"]), "--stage", "dev", "--out", str(out)])
    assert diagnose_main() == 0
    got = json.loads(out.read_text(encoding="utf-8"))
    assert got["per_arm"]["R7"]["valid_rate"] == 0.5
    assert got["per_arm"]["R7"]["group_macro_f1"] == 0.5
    assert got["per_arm"]["R7"]["zero_overlap_videos"] == 1


def test_frozen_input_verifier_detects_source_leakage(tmp_path, monkeypatch):
    inputs = tmp_path / "inputs"
    inputs.mkdir()
    base = {
        "video_id": "v", "youtube_id": "g", "split": "train",
        "pts_audit_status": "PASS", "temporal_mapping_status": "TEMPORAL_SECONDS_USABLE",
        "mapping_status": "usable", "spatial_mapping_status": "usable",
    }
    paths = {}
    for name in ("train", "dev", "confirm"):
        payload = []
        count = 1 if name == "train" else 96
        for index in range(count):
            item = dict(base, video_id=f"{name}{index}", youtube_id=f"{name}{index}",
                        split=name)
            payload.append(item)
        if name == "dev":
            payload[0]["youtube_id"] = "train0"
        path = inputs / f"{name}_temporal.jsonl"
        path.write_text("".join(json.dumps(x) + "\n" for x in payload), encoding="utf-8")
        paths[name] = path
    smoke = [dict(base, video_id=f"s{i}", youtube_id=f"sg{i}") for i in range(16)]
    smoke_path = inputs / "smoke_temporal.jsonl"
    smoke_path.write_text("".join(json.dumps(x) + "\n" for x in smoke), encoding="utf-8")
    paths["smoke"] = smoke_path
    hashes = {name: hashlib.sha256(path.read_bytes()).hexdigest()
              for name, path in paths.items()}
    (inputs / "split_freeze.json").write_text(
        json.dumps({"manifest_hashes": hashes}), encoding="utf-8")
    historical = tmp_path / "historical.jsonl"
    historical.write_text("".join(json.dumps({"youtube_id": f"h{i}"}) + "\n"
                                    for i in range(409)), encoding="utf-8")
    old_dev = tmp_path / "old_dev.jsonl"
    old_dev.write_text("", encoding="utf-8")
    output = tmp_path / "verification.json"
    monkeypatch.setattr(sys, "argv", ["verify_frozen_inputs.py", "--inputs", str(inputs),
        "--old-train", str(historical), "--old-dev", str(old_dev),
        "--output", str(output)])
    assert verify_frozen_inputs_main() == 2
    result = json.loads(output.read_text(encoding="utf-8"))
    assert "source_leakage:train:dev" in result["issues"]
