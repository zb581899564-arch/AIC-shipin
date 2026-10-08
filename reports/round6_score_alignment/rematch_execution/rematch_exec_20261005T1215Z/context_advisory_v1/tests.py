"""CPU contract tests for the new independent context channel."""
import json
import tempfile
from pathlib import Path
import context_contract as cc
import runtime as rt


def test_contracts():
    accepted = 0
    for n in (1, 2, 3, 10, 64):
        grammar = cc.OverviewGrammar(n)
        for first in range(n):
            for last in range(first, n):
                value = {"events": [{"first": first, "last": last, "description": "visible activity"}]}
                raw = json.dumps(value, separators=(",", ":"))
                assert grammar.complete(raw)
                assert cc.validate_overview(raw, list(map(float, range(n)))) == value
                for pos in range(len(raw) + 1):
                    assert grammar.valid_prefix(raw[:pos])
                assert not grammar.valid_prefix(raw + "x")
                accepted += 1
    base = {"first": 0, "last": 0, "description": "x"}
    valid = lambda events: json.dumps({"events": events}, separators=(",", ":"))
    assert cc.OverviewGrammar(64).complete(valid([]))
    assert cc.OverviewGrammar(64).complete(valid([base] * 8))
    rejected = [valid([base] * 9), valid([dict(base, first=64)]), valid([dict(base, last=-1)]),
        valid([dict(base, first=3, last=2)]), valid([dict(base, description=" ")]),
        valid([dict(base, description="x" * 81)]), valid([dict(base, description="中文")]),
        '{"events":[{"first":00,"last":0,"description":"x"}]}',
        '{"events":[{"first":0,"last":0,"description":"x"}]', valid([]) + " "]
    assert all(not cc.OverviewGrammar(64).complete(raw) for raw in rejected)
    assert cc.OverviewGrammar(64).complete(valid([dict(base, description="x" * 80)]))
    pts = [0.01, 0.03, 0.051, 0.09]
    plan = cc.overview_plan("/mock", "s", pts, 0.11, "ov")
    assert plan["planned_source_frame_ordinals"] == [0, 1, 2, 3]
    assert plan["planned_actual_pts_sec"] == pts
    assert plan["window_duration_sec"] == 0.1
    for n in (65, 67, 104, 500):
        p = cc.overview_plan("/mock", "s", list(map(float, range(n))), float(n), "ov")
        assert p["planned_source_frame_ordinals"] == [i * (n - 1) // 63 for i in range(64)]
        assert p["planned_actual_pts_sec"][-1] == n - 1
    mapped = json.loads(cc.render_event_table({"events": [base]}, pts, 0.03, 0.09))
    assert mapped["source_events"][0]["source_first_pts"] == 0.01
    assert mapped["sparse_overview_may_miss_local_events"]
    pairs = cc.deterministic_derangement(["a", "b", "c"], {"a": 3, "b": 2, "c": 1})
    assert all(k != v for k, v in pairs.items()) and set(pairs.values()) == set(pairs)
    with tempfile.TemporaryDirectory() as tmp:
        path = Path(tmp) / "raw.json"
        rt.raw_write(path, {"raw_output": "INVALID ANSWER"})
        assert json.loads(path.read_text())["raw_output"] == "INVALID ANSWER"
        try:
            rt.raw_write(path, {"raw_output": "overwritten"})
            raise AssertionError("overwrite accepted")
        except FileExistsError:
            pass
        assert json.loads(path.read_text())["raw_output"] == "INVALID ANSWER"
    assert cc.weak_metrics([], [ [0, 1] ])["f1"] == 0
    assert cc.weak_metrics([], [])["f1"] == 1
    assert cc.weak_metrics([[0, 2]], [[1, 3]])["f1"] == 0.5
    return {"status": "PASS_CPU_OVERVIEW_CONTRACTS_NOT_MODEL_GENERATION", "valid_boundary_pairs": accepted,
        "explicit_invalid_cases": len(rejected), "model_calls": 0, "optimizer_updates": 0}


if __name__ == "__main__":
    print(json.dumps(test_contracts()))
