"""Hand-computed boundary tests for the three-state temporal parser and prompt."""
from __future__ import annotations

import json
import unittest

from aic6.segments import (
    SegmentConstraint,
    SegmentState,
    build_prompt,
    check_label_cardinality,
    legacy_behavior,
    parse_response,
    union_length,
)

DUR = 10.0
FREE = SegmentConstraint(0, 5)


def parse(raw: str, *, duration: float = DUR, constraint: SegmentConstraint = FREE):
    return parse_response(raw, duration_sec=duration, constraint=constraint)


class ThreeStateTests(unittest.TestCase):
    def test_explicit_empty_is_valid_empty_not_a_failure(self):
        outcome = parse('{"segments":[]}')
        self.assertIs(outcome.state, SegmentState.VALID_EMPTY)
        self.assertEqual(outcome.segments, ())
        self.assertTrue(outcome.is_usable)

    def test_empty_below_min_segments_is_invalid(self):
        outcome = parse('{"segments":[]}', constraint=SegmentConstraint(1, 5))
        self.assertIs(outcome.state, SegmentState.INVALID)
        self.assertIn("empty_below_min_segments:1", outcome.reasons)

    def test_single_interval_is_valid_nonempty(self):
        outcome = parse('{"segments":[[1,2]]}')
        self.assertIs(outcome.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(outcome.segments, ((1.0, 2.0),))

    def test_five_intervals_at_the_configured_maximum(self):
        raw = json.dumps({"segments": [[i, i + 0.5] for i in range(5)]})
        outcome = parse(raw, constraint=SegmentConstraint(0, 5))
        self.assertIs(outcome.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(len(outcome.segments), 5)

    def test_six_and_seven_intervals_exceed_the_configured_maximum(self):
        for n in (6, 7):
            raw = json.dumps({"segments": [[i, i + 0.5] for i in range(n)]})
            outcome = parse(raw, constraint=SegmentConstraint(0, 5))
            self.assertIs(outcome.state, SegmentState.INVALID)
            self.assertIn(f"too_many_segments:{n}>5", outcome.reasons)

    def test_zero_maximum_rejects_every_interval(self):
        outcome = parse('{"segments":[[1,2]]}', constraint=SegmentConstraint(0, 0))
        self.assertIs(outcome.state, SegmentState.INVALID)
        self.assertIn("too_many_segments:1>0", outcome.reasons)
        self.assertIs(parse('{"segments":[]}', constraint=SegmentConstraint(0, 0)).state,
                      SegmentState.VALID_EMPTY)

    def test_reversed_interval_is_invalid(self):
        outcome = parse('{"segments":[[2,1]]}')
        self.assertIs(outcome.state, SegmentState.INVALID)
        self.assertIn("segment_0_not_0_le_start_lt_end", outcome.reasons)

    def test_duration_tolerance_boundary(self):
        # 10.0005 is inside duration + 1e-3 and is clamped to 10.0; 10.002 is outside -> invalid.
        ok = parse('{"segments":[[0,10.0005]]}')
        self.assertIs(ok.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(ok.segments, ((0.0, 10.0),))
        bad = parse('{"segments":[[0,10.002]]}')
        self.assertIs(bad.state, SegmentState.INVALID)
        self.assertIn("segment_0_exceeds_duration", bad.reasons)

    def test_bool_and_non_numeric_bounds_are_invalid(self):
        for raw in ('{"segments":[[true,2]]}', '{"segments":[["0",2]]}',
                    '{"segments":[[null,2]]}'):
            outcome = parse(raw)
            self.assertIs(outcome.state, SegmentState.INVALID, msg=raw)
            self.assertTrue(any("non_numeric" in r for r in outcome.reasons), msg=outcome.reasons)

    def test_nan_and_infinity_are_invalid(self):
        for token in ("NaN", "Infinity", "-Infinity"):
            outcome = parse('{"segments":[[0,%s]]}' % token)
            self.assertIs(outcome.state, SegmentState.INVALID, msg=token)

    def test_empty_output_and_unparseable_text_are_invalid(self):
        for raw in ("", "   ", "no json here", '{"segments": 3}', "{}", "[1,2,3]"):
            outcome = parse(raw)
            self.assertIs(outcome.state, SegmentState.INVALID, msg=repr(raw))

    def test_overlapping_segments_warn_but_stay_valid_and_sorted(self):
        outcome = parse('{"segments":[[3,8],[0,5]]}')
        self.assertIs(outcome.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(outcome.segments, ((0.0, 5.0), (3.0, 8.0)))
        self.assertTrue(outcome.warnings)

    def test_historical_fenced_text_still_parses(self):
        outcome = parse('```json\n{"segments":[[1,2]]}\n```')
        self.assertIs(outcome.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(outcome.segments, ((1.0, 2.0),))

    def test_historical_prose_wrapped_object_still_parses(self):
        outcome = parse('Here you go: {"segments":[[0,1]]} done')
        self.assertIs(outcome.state, SegmentState.VALID_NONEMPTY)
        self.assertEqual(outcome.decode_path, "historical_object_scan")
        self.assertEqual(outcome.segments, ((0.0, 1.0),))

    def test_ambiguous_multiple_objects_are_invalid(self):
        outcome = parse('{"segments":[[0,1]]} {"segments":[[2,3]]}')
        self.assertIs(outcome.state, SegmentState.INVALID)
        self.assertTrue(any("ambiguous" in r for r in outcome.reasons), msg=outcome.reasons)


class PromptTests(unittest.TestCase):
    def test_prompt_is_shared_and_configured_by_one_constraint(self):
        prompt = build_prompt(duration_sec=30.0, constraint=SegmentConstraint(0, 5))
        self.assertIn("between 0 and 5 intervals", prompt)
        self.assertIn('{"segments":[]}', prompt)
        self.assertIn("0 <= start_sec < end_sec <= 30.000000", prompt)

    def test_prompt_hides_the_empty_option_when_min_segments_is_positive(self):
        prompt = build_prompt(duration_sec=30.0, constraint=SegmentConstraint(1, 3))
        self.assertIn("between 1 and 3 intervals", prompt)
        self.assertNotIn('{"segments":[]}', prompt)

    def test_prompt_rejects_non_positive_duration(self):
        for bad in (0.0, -1.0, float("nan")):
            with self.assertRaises(ValueError):
                build_prompt(duration_sec=bad, constraint=FREE)


class ConstraintAndLabelTests(unittest.TestCase):
    def test_invalid_constraints_are_rejected(self):
        for lo, hi in ((-1, 5), (0, -1), (3, 2)):
            with self.assertRaises(ValueError):
                SegmentConstraint(lo, hi)

    def test_seven_segment_label_is_reported_and_left_untouched(self):
        rows = [
            {"sample_id": "a", "row_index": 1, "segments_clip_local": [[0, 1]]},
            {"sample_id": "b", "row_index": 2, "segments_clip_local": [[0, 1], [2, 3]]},
            {"sample_id": "c", "row_index": 3,
             "segments_clip_local": [[i, i + 0.5] for i in range(7)]},
        ]
        before = json.dumps(rows, sort_keys=True)
        report = check_label_cardinality(rows, constraint=SegmentConstraint(0, 5))
        self.assertEqual(report["n_rows"], 3)
        self.assertEqual(report["histogram"], {"1": 1, "2": 1, "7": 1})
        self.assertEqual(report["n_violations"], 1)
        self.assertEqual(report["violations"][0]["sample_id"], "c")
        self.assertEqual(report["violations"][0]["action"], "REPORTED_UNCHANGED")
        self.assertEqual(json.dumps(rows, sort_keys=True), before)  # never edited

    def test_union_length(self):
        # [0,2) and [1,3) union to [0,3) = 3.0; adjacent [3,5) extends to 5.0.
        self.assertAlmostEqual(union_length([[0, 2], [1, 3]]), 3.0, places=9)
        self.assertAlmostEqual(union_length([[0, 2], [3, 5]]), 4.0, places=9)
        self.assertEqual(union_length([]), 0.0)


class LegacyBehaviourTests(unittest.TestCase):
    def test_legacy_treats_empty_as_failure_and_reports_its_reason(self):
        out = legacy_behavior('{"segments":[]}', duration_sec=DUR)
        self.assertFalse(out["legacy_output_valid"])
        self.assertEqual(out["legacy_reason"], "'segments' is empty")

    def test_legacy_accepts_non_empty(self):
        out = legacy_behavior('{"segments":[[1,2]]}', duration_sec=DUR)
        self.assertTrue(out["legacy_output_valid"])
        self.assertEqual(out["legacy_segments"], [[1.0, 2.0]])

    def test_legacy_rejects_too_many_segments(self):
        raw = json.dumps({"segments": [[i, i + 0.5] for i in range(6)]})
        out = legacy_behavior(raw, duration_sec=DUR, max_segments=5)
        self.assertFalse(out["legacy_output_valid"])


if __name__ == "__main__":
    unittest.main()
