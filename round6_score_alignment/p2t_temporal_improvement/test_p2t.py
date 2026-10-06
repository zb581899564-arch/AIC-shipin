from temporal_diagnostics import group_bootstrap, stats, union
from decide_gate import decide


def test_union_and_endpoint_semantics():
    assert union([[2, 4], [0, 1], [1, 3]]) == [[0, 4]]
    assert union([[0, 1], [1.0001, 2]]) == [[0, 1], [1.0001, 2]]


def test_metric_boundaries():
    assert stats([], [])["f1"] == 1
    assert stats([], [[0, 1]])["f1"] == 0
    assert stats([[0, 1]], [[0, 1]])["f1"] == 1
    got = stats([[0, 2]], [[1, 3]])
    assert got["precision"] == 0.5 and got["recall"] == 0.5 and got["f1"] == 0.5


def test_invalid_zero_overlap():
    got = stats([], [[1, 2]])
    assert got["zero_overlap"] and got["duration_ratio"] == 0


def test_bootstrap_constant_difference():
    assert group_bootstrap([0.25] * 8, draws=1000, seed=7) == [0.25, 0.25]


def test_gate_all_conditions_required():
    base = {"group_macro_f1": 0.45, "valid_rate": 0.9}
    good = {"group_macro_f1": 0.55, "valid_rate": 1.0}
    data = {"per_arm": {"BASE": base, "P2T_FRESH": good},
            "paired": {"P2T_FRESH_minus_BASE": {"mean": 0.10, "ci95": [0.02, 0.18]}}}
    assert decide(data)["status"] == "ACCEPT_P2T_FRESH"
    data["paired"]["P2T_FRESH_minus_BASE"]["ci95"][0] = -0.01
    assert decide(data)["status"] == "STOP_KEEP_BASE"
