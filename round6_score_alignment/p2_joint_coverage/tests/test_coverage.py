"""P2 boundary tests: four-state coverage, bounded reuse, gate and geometry.

Expected values are hand-computed literals; nothing is derived from the
implementation under test.
"""
from __future__ import annotations

import unittest

from aic6.coverage import (
    AuditResult,
    CoverageError,
    CoverageGate,
    CoverageState,
    FrameAuditRow,
    ShotIntervals,
    audit_frames,
    legacy_copy_profile,
    validate_max_reuse_gap,
)
from aic6.scoring import box_from_xyw, spatial_iou


class TestGapValidation(unittest.TestCase):
    def test_nan_rejected(self):
        with self.assertRaises(CoverageError):
            validate_max_reuse_gap(float("nan"))

    def test_inf_rejected(self):
        with self.assertRaises(CoverageError):
            validate_max_reuse_gap(float("inf"))

    def test_bool_rejected(self):
        with self.assertRaises(CoverageError):
            validate_max_reuse_gap(True)

    def test_float_rejected(self):
        with self.assertRaises(CoverageError):
            validate_max_reuse_gap(30.0)

    def test_zero_and_negative_rejected(self):
        for value in (0, -1):
            with self.assertRaises(CoverageError):
                validate_max_reuse_gap(value)

    def test_positive_int_accepted(self):
        self.assertEqual(validate_max_reuse_gap(30), 30)

    def test_none_means_same_frame_only(self):
        self.assertIsNone(validate_max_reuse_gap(None))


class TestAuditFrames(unittest.TestCase):
    SHOTS = [(0, 40), (40, 100)]

    def test_same_frame_wins(self):
        audit = audit_frames(selected_frames=[10], source_boxes={10: [5, 6, 100]},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=30)
        self.assertEqual(audit.counts[CoverageState.SAME_FRAME.value], 1)
        self.assertEqual(audit.rows[0].source_frame, 10)
        self.assertEqual(audit.rows[0].distance, 0)

    def test_within_shot_nearest_within_limit(self):
        audit = audit_frames(selected_frames=[12], source_boxes={10: [5, 6, 100]},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=30)
        self.assertEqual(audit.counts[CoverageState.SHOT_NEAREST.value], 1)
        row = audit.rows[0]
        self.assertEqual(row.source_frame, 10)
        self.assertEqual(row.distance, 2)
        self.assertEqual(row.shot, (0, 40))
        self.assertFalse(row.crosses_shot_boundary)

    def test_within_shot_over_limit_requires_inference(self):
        # nearest source in shot (0,40) is frame 10, distance 35 > 30
        audit = audit_frames(selected_frames=[45], source_boxes={10: [5, 6, 100]},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=30)
        self.assertEqual(audit.counts[CoverageState.NEEDS_INFERENCE.value], 1)
        self.assertIsNone(audit.rows[0].box)

    def test_source_in_other_shot_never_reused(self):
        # frame 45 sits inside shot (40,100) whose only declared sources are in
        # shot (0,40); even with a generous limit of 40 the copy must be refused
        audit = audit_frames(selected_frames=[45], source_boxes={10: [5, 6, 100]},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=40)
        self.assertEqual(audit.counts[CoverageState.NEEDS_INFERENCE.value], 1)
        # the frame IS inside a declared shot that has no source of its own:
        # refusal reason must name the within-shot gap, not a missing shot
        self.assertTrue(audit.rows[0].note.startswith("within-shot") or
                        audit.rows[0].note.startswith("inside a declared shot"),
                        msg=audit.rows[0].note)
        self.assertIsNone(audit.rows[0].box)

    def test_no_shot_info_fails_closed(self):
        audit = audit_frames(selected_frames=[12], source_boxes={10: [5, 6, 100]},
                             n_frames=100, shots=None, max_reuse_gap_frames=30)
        self.assertEqual(audit.counts[CoverageState.NEEDS_INFERENCE.value], 1)
        self.assertIn("no shot declared", audit.rows[0].note)

    def test_no_source_at_all_is_unresolvable(self):
        audit = audit_frames(selected_frames=[12], source_boxes={},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=30)
        self.assertEqual(audit.counts[CoverageState.UNRESOLVABLE.value], 1)

    def test_frame_out_of_range_rejected(self):
        with self.assertRaises(CoverageError):
            audit_frames(selected_frames=[100], source_boxes={}, n_frames=100,
                         shots=self.SHOTS, max_reuse_gap_frames=30)

    def test_nearest_tie_prefers_earlier_frame(self):
        # sources at 8 and 12, frame 10: tie -> min by (distance, frame) = 8
        audit = audit_frames(selected_frames=[10], source_boxes={8: [1, 1, 10], 12: [2, 2, 10]},
                             n_frames=100, shots=self.SHOTS, max_reuse_gap_frames=30)
        self.assertEqual(audit.rows[0].source_frame, 8)


class TestLegacyCopyProfile(unittest.TestCase):
    def test_distances_recorded(self):
        profile = legacy_copy_profile(selected_frames=[10, 12, 200],
                                      source_boxes={10: [1, 1, 10]},
                                      n_frames=300, shots=[(0, 100), (100, 300)])
        self.assertEqual(profile["n_same_frame"], 1)
        self.assertEqual(profile["n_copied"], 2)
        self.assertEqual(profile["distance_min"], 2)          # frame 12 -> 10
        self.assertEqual(profile["distance_max"], 190)        # frame 200 -> 10
        self.assertEqual(profile["n_over_30_frames"], 1)

    def test_shot_crossing_counted(self):
        profile = legacy_copy_profile(selected_frames=[150], source_boxes={10: [1, 1, 10]},
                                      n_frames=300, shots=[(0, 100), (100, 300)])
        self.assertEqual(profile["n_copied"], 1)
        self.assertEqual(profile["n_crossing_declared_shot_boundary"], 1)

    def test_no_copy_when_all_same_frame(self):
        profile = legacy_copy_profile(selected_frames=[10], source_boxes={10: [1, 1, 10]},
                                      n_frames=300, shots=None)
        self.assertEqual(profile["n_copied"], 0)


class TestGate(unittest.TestCase):
    def test_gate_requires_declared_limit_for_bounded_reuse(self):
        with self.assertRaises(CoverageError):
            CoverageGate(allow_bounded_within_shot=True, max_reuse_gap_frames=None)

    def test_gate_deliverable_all_same_frame(self):
        audit = audit_frames(selected_frames=[1, 2], source_boxes={1: [0, 0, 5], 2: [0, 0, 5]},
                             n_frames=10, shots=None)
        verdict = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        self.assertTrue(verdict["deliverable"])

    def test_gate_blocks_needs_inference(self):
        audit = audit_frames(selected_frames=[5], source_boxes={1: [0, 0, 5]},
                             n_frames=10, shots=[(0, 10)], max_reuse_gap_frames=2)
        verdict = CoverageGate(allow_bounded_within_shot=True, max_reuse_gap_frames=2).judge(audit)
        self.assertFalse(verdict["deliverable"])
        self.assertEqual(verdict["verdict"], "NEEDS_SPATIAL_INFERENCE")

    def test_gate_empty_selection(self):
        audit = audit_frames(selected_frames=[], source_boxes={}, n_frames=10, shots=None)
        verdict = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        self.assertEqual(verdict["verdict"], "EMPTY_SELECTION")
        self.assertFalse(verdict["deliverable"])


class TestSupervisorRegression20260918(unittest.TestCase):
    """Two bypass cases recorded in SUPERVISOR_REVIEW_20260918.md.

    Regression first: both must fail closed after the distance-contract fix.
    """

    def test_no_gap_limit_refuses_within_shot_reuse(self):
        # case 1: shots declared, max_reuse_gap_frames=None -> the audit must NOT
        # return SHOT_NEAREST (distance 89 was previously copied unbounded) and
        # the gate must not deliver
        audit = audit_frames(selected_frames=[90], source_boxes={1: [0, 0, 50]},
                             n_frames=100, shots=[(0, 100)], max_reuse_gap_frames=None)
        self.assertEqual(audit.counts[CoverageState.SHOT_NEAREST.value], 0)
        self.assertEqual(audit.counts[CoverageState.NEEDS_INFERENCE.value], 1)
        self.assertIsNone(audit.rows[0].box)
        verdict = CoverageGate(allow_bounded_within_shot=False).judge(audit)
        self.assertEqual(verdict["verdict"], "NEEDS_SPATIAL_INFERENCE")
        self.assertFalse(verdict["deliverable"])

    def test_gate_reverifies_rows_against_its_own_limit(self):
        # case 2: the audit ran with a limit of 100 (distance 89 passes there),
        # but THIS gate declares a limit of 1 -> the gate must re-verify each row
        # and refuse delivery instead of trusting the audit's labels
        audit = audit_frames(selected_frames=[90], source_boxes={1: [0, 0, 50]},
                             n_frames=100, shots=[(0, 100)], max_reuse_gap_frames=100)
        self.assertEqual(audit.counts[CoverageState.SHOT_NEAREST.value], 1)
        verdict = CoverageGate(allow_bounded_within_shot=True,
                               max_reuse_gap_frames=1).judge(audit)
        self.assertEqual(verdict["verdict"], "NEEDS_SPATIAL_INFERENCE")
        self.assertFalse(verdict["deliverable"])
        self.assertEqual(len(verdict["policy_violations"]), 1)
        self.assertEqual(verdict["policy_violations"][0]["distance"], 89)

    def test_gate_accepts_legitimate_bounded_reuse(self):
        # control: distance 2 with a limit of 30 stays deliverable
        audit = audit_frames(selected_frames=[12], source_boxes={10: [0, 0, 50]},
                             n_frames=100, shots=[(0, 40), (40, 100)],
                             max_reuse_gap_frames=30)
        verdict = CoverageGate(allow_bounded_within_shot=True,
                                max_reuse_gap_frames=30).judge(audit)
        self.assertTrue(verdict["deliverable"])
        self.assertEqual(verdict["policy_violations"], [])


class TestSupervisorRegressionV2(unittest.TestCase):
    def test_same_frame_must_have_its_own_box_and_source(self):
        for box, source_frame, distance in (
            (None, 10, 0),
            ([0, 0, 10], 9, 0),
            ([0, 0, 10], 10, 1),
        ):
            with self.subTest(box=box, source_frame=source_frame, distance=distance):
                audit = AuditResult(video_id="v", n_frames=100, rows=[FrameAuditRow(
                    frame=10, state=CoverageState.SAME_FRAME.value, box=box,
                    source_frame=source_frame, distance=distance, shot=None,
                    crosses_shot_boundary=False, note="forged")])
                verdict = CoverageGate(allow_bounded_within_shot=False).judge(audit)
                self.assertFalse(verdict["deliverable"])
                self.assertEqual(len(verdict["policy_violations"]), 1)

    def test_nearest_must_recompute_distance_and_stay_in_shot(self):
        cases = (
            (1, 1, (80, 100), False),  # claimed distance 1; actual distance 89
            (89, 1, (90, 100), False),  # source outside declared shot
            (89, 1, (80, 100), True),   # crossing flag contradicts reuse
            (90, 0, (80, 100), False),  # same frame must not be a reuse
        )
        for source_frame, distance, shot, crossing in cases:
            with self.subTest(source_frame=source_frame, distance=distance,
                              shot=shot, crossing=crossing):
                audit = AuditResult(video_id="v", n_frames=100, rows=[FrameAuditRow(
                    frame=90, state=CoverageState.SHOT_NEAREST.value,
                    box=[0, 0, 10], source_frame=source_frame,
                    distance=distance, shot=shot,
                    crosses_shot_boundary=crossing, note="forged")])
                verdict = CoverageGate(allow_bounded_within_shot=True,
                                       max_reuse_gap_frames=1).judge(audit)
                self.assertFalse(verdict["deliverable"])
                self.assertEqual(len(verdict["policy_violations"]), 1)


class TestShotIntervals(unittest.TestCase):
    def test_overlap_rejected(self):
        with self.assertRaises(CoverageError):
            ShotIntervals(shots_by_video={"v": ((0, 40), (30, 100))})

    def test_bad_bounds_rejected(self):
        with self.assertRaises(CoverageError):
            ShotIntervals(shots_by_video={"v": ((40, 40),)})
        with self.assertRaises(CoverageError):
            ShotIntervals(shots_by_video={"v": ((-1, 10),)})


class TestGeometryBothOrientations(unittest.TestCase):
    """9:16 and 16:9 legality of derived boxes (h = w * th / tw)."""

    def test_9x16_max_width(self):
        # 534x300 frame, 9:16 target: cw = floor(300*9/16) = 168
        box = box_from_xyw([183, 0, 168], ratio_wh=[9, 16], width=534, height=300,
                           location="t")
        self.assertEqual((box.w, box.h), (168, 168 * 16 / 9))
        self.assertLessEqual(box.y + box.h, 300 + 1e-9)

    def test_9x16_width_169_illegal(self):
        # 169 wide -> h = 300.44 > 300: must be rejected
        with self.assertRaises(ValueError):
            box_from_xyw([183, 0, 169], ratio_wh=[9, 16], width=534, height=300,
                         location="t")

    def test_16x9_max_height(self):
        # 720x1280 frame, 16:9 target: full width legal, h = 720*9/16 = 405
        box = box_from_xyw([0, 100, 720], ratio_wh=[16, 9], width=720, height=1280,
                           location="t")
        self.assertEqual((box.w, box.h), (720, 405.0))

    def test_16x9_overflow_rejected(self):
        with self.assertRaises(ValueError):
            box_from_xyw([0, 900, 720], ratio_wh=[16, 9], width=720, height=1280,
                         location="t")

    def test_iou_identical_boxes_is_one(self):
        a = box_from_xyw([10, 10, 50], ratio_wh=[9, 16], width=534, height=300, location="a")
        b = box_from_xyw([10, 10, 50], ratio_wh=[9, 16], width=534, height=300, location="b")
        self.assertAlmostEqual(spatial_iou(a, b), 1.0)

    def test_iou_disjoint_is_zero(self):
        a = box_from_xyw([0, 0, 50], ratio_wh=[9, 16], width=534, height=300, location="a")
        b = box_from_xyw([400, 0, 50], ratio_wh=[9, 16], width=534, height=300, location="b")
        self.assertEqual(spatial_iou(a, b), 0.0)


if __name__ == "__main__":
    unittest.main()
