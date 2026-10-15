"""One targeted pure check for half-open native selection and five ablations."""
from fractions import Fraction as F
from combine_events import combine


def main():
    clocks = {"source": {"normalized_exact_pts": [str(F(i, 4)) for i in range(80)],
                         "physical_end_exact": "20"}}
    events = [dict(event_id="a", source_id="source", original_interval_exact=["4", "12"],
                   original_window_exact=["0", "20"], physical_end_exact="20"),
              dict(event_id="b", source_id="source", original_interval_exact=["10", "14"],
                   original_window_exact=["0", "20"], physical_end_exact="20")]
    endpoints = {}
    for event in events:
        for side, value in zip(("start", "end"), event["original_interval_exact"]):
            endpoints[event["event_id"] + "." + side] = dict(
                event_id=event["event_id"], side=side, original_endpoint_exact=value,
                endpoint_exact=value, applied_decision="UNKNOWN")
    verification = {e["event_id"]: {"event_id": e["event_id"], "decision": "UNKNOWN"} for e in events}
    baseline = combine(events, endpoints, verification, clocks)
    assert all(x["selected_ordinals"] == baseline["START"]["selected_ordinals"] for x in baseline.values())
    # Original8s eligibility stays true after refinement shortens it to6s.
    endpoints["a.start"].update(endpoint_exact="5", applied_decision="REFINE")
    endpoints["a.end"].update(endpoint_exact="11", applied_decision="REFINE")
    verification["a"]["decision"] = "DROP"
    result = combine(events, endpoints, verification, clocks)
    both_a = result["BOTH"]["decisions"][0]
    assert both_a["selected_interval_exact"] == ["17/4", "47/4"]
    assert both_a["original_length_padding_eligible"] is True
    assert result["VERIFY"]["selected_ordinals"]["source"] == list(range(37, 58))
    # Overlap remains supported by retained b; exact exclusive14.5 is excluded.
    assert 44 in result["VERIFY"]["selected_ordinals"]["source"]
    assert 58 not in result["VERIFY"]["selected_ordinals"]["source"]
    assert len({tuple(x["selected_ordinals"]["source"]) for x in result.values()}) >= 3
    endpoints["a.start"].update(endpoint_exact="12", applied_decision="UNKNOWN")
    try:
        combine(events, endpoints, verification, clocks)
    except ValueError:
        pass
    else:
        raise AssertionError("A fake UNKNOWN changing cut was accepted")
    print("PASS pure five-ablation union/padding/native-endpoint check; real inputs/model/ZIP0")


if __name__ == "__main__":
    main()
