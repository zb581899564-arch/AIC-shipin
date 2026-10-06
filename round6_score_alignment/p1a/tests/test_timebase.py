"""Hand-computed boundary tests for the single time-conversion module."""
from __future__ import annotations

import math
import unittest

from aic6.timebase import (
    CfrTimeline,
    TimeConvention,
    TimebaseError,
    VfrRequiresPts,
    VfrTimeline,
    compare_conventions,
    frames_to_intervals,
    local_interval_to_absolute,
    merge_frames,
    select_frames_legacy_ceil_halfopen,
    select_frames_legacy_round_inclusive,
    select_frames_timestamp_halfopen,
)


class TimestampHalfOpenTests(unittest.TestCase):
    def test_integer_fps_one_second_is_30_frames(self):
        # fps=30, [10.0, 11.0): frames with 10.0 <= f/30 < 11.0 -> 300..329 -> 30 frames.
        sel = select_frames_timestamp_halfopen(a_sec=10.0, b_sec=11.0,
                                               timeline=CfrTimeline(fps=30.0, n_frames=630))
        self.assertEqual(len(sel.frames), 30)
        self.assertEqual(sel.first_frame, 300)
        self.assertEqual(sel.last_frame, 329)
        self.assertEqual(sel.convention, TimeConvention.TIMESTAMP_HALFOPEN.value)

    def test_non_integer_fps_2997(self):
        # fps=29.97002997..., [0.0, 1.0): frames with f/29.97 < 1.0 -> f < 29.97 -> 0..29 (30).
        fps = 29.97002997002997
        sel = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=1.0,
                                               timeline=CfrTimeline(fps=fps, n_frames=1000))
        self.assertEqual(len(sel.frames), 30)
        self.assertEqual((sel.first_frame, sel.last_frame), (0, 29))

    def test_non_integer_fps_23976(self):
        # fps=23.976, [0.0, 1.0): frames with f/23.976 < 1.0 -> f < 23.976 -> 0..23 (24).
        sel = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=1.0,
                                               timeline=CfrTimeline(fps=23.976, n_frames=3597))
        self.assertEqual(len(sel.frames), 24)
        self.assertEqual((sel.first_frame, sel.last_frame), (0, 23))

    def test_window_origin_offset_changes_absolute_interval(self):
        # fps=29.97, window start 30.0 -> first visible frame = ceil(30.0*29.97) = 900
        # (30*29.97002997 = 899.1008991 -> ceil 900).  Local [0,1) therefore maps to
        # [900/29.97, 930/29.97) -> frames 900..929 (30 frames), not 899..929 (31).
        fps = 29.97002997002997
        a_abs, b_abs, origin = local_interval_to_absolute(
            a_local_sec=0.0, b_local_sec=1.0, window_start_sec=30.0, fps=fps,
            n_frames=6000, use_sampling_origin=True)
        self.assertEqual(origin, 900)
        self.assertAlmostEqual(a_abs, 900.0 / fps, places=9)
        self.assertAlmostEqual(b_abs - a_abs, 1.0, places=9)
        sel = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=1.0,
                                               timeline=CfrTimeline(fps=fps, n_frames=6000),
                                               origin_frame=origin)
        self.assertEqual((sel.first_frame, sel.last_frame, len(sel.frames)), (900, 929, 30))
        legacy = select_frames_legacy_round_inclusive(a_sec=30.0, b_sec=31.0, fps=fps, n_frames=6000)
        self.assertEqual((legacy.first_frame, legacy.last_frame, len(legacy.frames)), (899, 929, 31))
        self.assertEqual(sel.first_frame - legacy.first_frame, 1)

    def test_video_last_frame_is_inclusive_of_n_minus_1(self):
        # fps=25, n=10, [0.2, 0.4): frames 5..9 (10.0/25 = 0.4 is excluded) -> 5 frames, last = n-1.
        sel = select_frames_timestamp_halfopen(a_sec=0.2, b_sec=0.4,
                                               timeline=CfrTimeline(fps=25.0, n_frames=10))
        self.assertEqual((sel.first_frame, sel.last_frame, len(sel.frames)), (5, 9, 5))

    def test_interval_past_the_end_is_empty(self):
        # fps=25, n=10, [1.0, 2.0) -> lower bound 25 already past n -> empty, never an error.
        sel = select_frames_timestamp_halfopen(a_sec=1.0, b_sec=2.0,
                                               timeline=CfrTimeline(fps=25.0, n_frames=10))
        self.assertTrue(sel.empty)
        self.assertEqual(sel.frames, ())

    def test_adjacent_windows_do_not_overlap_or_gap(self):
        # fps=30: [0,1) -> 0..29 and [1,2) -> 30..59; half-open gives no overlap, no gap.
        first = select_frames_timestamp_halfopen(a_sec=0.0, b_sec=1.0,
                                                 timeline=CfrTimeline(fps=30.0, n_frames=630))
        second = select_frames_timestamp_halfopen(a_sec=1.0, b_sec=2.0,
                                                  timeline=CfrTimeline(fps=30.0, n_frames=630))
        self.assertEqual((first.last_frame, second.first_frame), (29, 30))
        self.assertEqual(set(first.frames) & set(second.frames), set())
        self.assertEqual(frames_to_intervals(merge_frames(first.frames, second.frames)),
                         ((0, 59),))

    def test_sampling_origin_frame_is_clamped(self):
        # window start far past the end: origin clamps to n-1 = 99.
        self.assertEqual(CfrTimeline(fps=30.0, n_frames=100).sampling_origin_frame(1000.0), 99)

    def test_illegal_frame_indices_are_rejected(self):
        timeline = CfrTimeline(fps=30.0, n_frames=10)
        for bad in (10, -1, True, 1.5, "1"):
            with self.assertRaises(TimebaseError):
                timeline.check_frame(bad)  # type: ignore[arg-type]

    def test_non_positive_fps_and_frame_count_are_rejected(self):
        for fps, n in ((0.0, 10), (-30.0, 10), (float("nan"), 10), (30.0, 0), (30.0, -1)):
            with self.assertRaises(TimebaseError):
                CfrTimeline(fps=fps, n_frames=n)

    def test_reversed_or_equal_interval_is_rejected(self):
        timeline = CfrTimeline(fps=30.0, n_frames=100)
        for a, b in ((1.0, 1.0), (2.0, 1.0)):
            with self.assertRaises(TimebaseError):
                select_frames_timestamp_halfopen(a_sec=a, b_sec=b, timeline=timeline)
        with self.assertRaises(TimebaseError):
            select_frames_legacy_round_inclusive(a_sec=1.0, b_sec=1.0, fps=30.0, n_frames=100)


class LegacyConventionTests(unittest.TestCase):
    def test_ceil_halfopen_matches_timestamp_policy_without_window_offset(self):
        # Both select the frames whose timestamps lie in [a,b); they must agree when the
        # window starts at 0 (origin frame 0).
        for fps, a, b in ((30.0, 10.0, 11.0), (29.97002997002997, 0.0, 1.0), (23.976, 3.0, 3.5)):
            new = select_frames_timestamp_halfopen(a_sec=a, b_sec=b,
                                                   timeline=CfrTimeline(fps=fps, n_frames=10000))
            legacy = select_frames_legacy_ceil_halfopen(a_sec=a, b_sec=b, fps=fps, n_frames=10000)
            self.assertEqual(new.frames, legacy.frames, msg=f"fps={fps} interval=[{a},{b})")

    def test_round_inclusive_adds_the_endpoint_frame(self):
        # fps=30, [10.0,11.0): round(300)=300, round(330)=330 -> 300..330 inclusive = 31 frames,
        # versus 30 under the half-open policy: exactly the +1 end frame seen in round 5.
        legacy = select_frames_legacy_round_inclusive(a_sec=10.0, b_sec=11.0, fps=30.0, n_frames=630)
        self.assertEqual((legacy.first_frame, legacy.last_frame, len(legacy.frames)), (300, 330, 31))

    def test_round_inclusive_clamps_to_n_minus_1(self):
        # round(10.0 * 30) = 300 already >= n -> clamp to n-1 = 9, and fb <= fa repair keeps 1 frame.
        legacy = select_frames_legacy_round_inclusive(a_sec=10.0, b_sec=10.1, fps=30.0, n_frames=10)
        self.assertEqual(legacy.frames, (9,))

    def test_legacy_invalid_input_raises_instead_of_guessing(self):
        with self.assertRaises(TimebaseError):
            select_frames_timestamp_halfopen(a_sec=float("nan"), b_sec=1.0,
                                             timeline=CfrTimeline(fps=30.0, n_frames=10))
        with self.assertRaises(TimebaseError):
            select_frames_legacy_ceil_halfopen(a_sec=float("inf"), b_sec=1.0, fps=30.0, n_frames=10)

    def test_compare_conventions_reports_all_three(self):
        out = compare_conventions(a_sec=10.0, b_sec=11.0, fps=30.0, n_frames=630)
        self.assertEqual(out["timestamp_halfopen"]["n_frames"], 30)
        self.assertEqual(out["legacy_ceil_halfopen"]["n_frames"], 30)
        self.assertEqual(out["legacy_round_inclusive"]["n_frames"], 31)


class VfrTests(unittest.TestCase):
    def test_explicit_pts_is_honoured_half_open(self):
        # PTS = [0.0, 0.25, 0.5, 0.75] (all exactly representable); local [0.25, 0.75) with
        # origin frame 1 maps to absolute [0.5, 1.0) -> indices with t in range -> 2, 3.
        timeline = VfrTimeline(pts_sec=[0.0, 0.25, 0.5, 0.75])
        sel = select_frames_timestamp_halfopen(a_sec=0.25, b_sec=0.75, timeline=timeline,
                                               origin_frame=1)
        self.assertEqual(sel.frames, (2, 3))
        self.assertEqual(sel.detail["timeline"], "vfr_pts")

    def test_vfr_without_pts_is_refused(self):
        with self.assertRaises(VfrRequiresPts):
            VfrTimeline(pts_sec=None)  # type: ignore[arg-type]

    def test_vfr_rejects_non_monotonic_and_non_finite_pts(self):
        for pts in ([0.0, 0.2, 0.1], [0.0, float("nan")], []):
            with self.assertRaises(TimebaseError):
                VfrTimeline(pts_sec=pts)

    def test_vfr_frame_indices_are_bounded(self):
        timeline = VfrTimeline(pts_sec=[0.0, 0.04, 0.08])
        with self.assertRaises(TimebaseError):
            timeline.check_frame(3)


class HelperTests(unittest.TestCase):
    def test_intervals_and_merge(self):
        self.assertEqual(frames_to_intervals((0, 1, 2, 5)), ((0, 2), (5, 5)))
        self.assertEqual(merge_frames((3, 1), (2, 9)), (1, 2, 3, 9))
        self.assertEqual(frames_to_intervals(()), ())

    def test_origin_offset_is_zero_for_exact_multiples_and_subframe_otherwise(self):
        # fps=25, start=30.0 -> 30*25 = 750 exactly -> origin offset 0.
        _a, _b, origin = local_interval_to_absolute(a_local_sec=0.0, b_local_sec=1.0,
                                                    window_start_sec=30.0, fps=25.0, n_frames=1000)
        self.assertEqual(origin, 750)
        self.assertTrue(math.isclose(origin / 25.0 - 30.0, 0.0, abs_tol=1e-12))
        # fps=23.976, start=13.5 -> 13.5*23.976 = 323.676 -> origin 324 -> offset 0.0135..., and
        # the invariant is 0 <= offset < 1/fps.
        fps = 23.976
        _a2, _b2, origin2 = local_interval_to_absolute(
            a_local_sec=0.0, b_local_sec=1.0, window_start_sec=13.5, fps=fps, n_frames=1000)
        self.assertEqual(origin2, 324)
        offset = origin2 / fps - 13.5
        self.assertTrue(0.0 < offset < 1.0 / fps)


if __name__ == "__main__":
    unittest.main()
