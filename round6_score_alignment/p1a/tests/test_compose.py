"""Hand-computed tests for composition and spatial provenance.

Synthetic setup (no video is decoded anywhere):
  fps = 30, n_frames = 600 (20 s); the spatial source has boxes at frames 0,1,2,3 only.
  declared shots: [0,10), [10,20), [20,600)
  one window starts at 0.0 s and lasts 11.0 s with intervals [[0,0.2],[0.2,0.4],[10.0,10.2]]

  new policy frame selection (origin frame 0):
    [0.0,0.2) -> 0..5 ; [0.2,0.4) -> 6..11 ; [10.0,10.2) -> 300..305   (18 frames)
  legacy round-inclusive selection:
    [0.0,0.2) -> 0..6 ; [0.2,0.4) -> 6..12 ; [10.0,10.2) -> 300..306   (20 frames)

  provenance under the new mode with the declared shot map:
    frames 0-3      -> SOURCE_SAME_FRAME (4)
    frames 4-9      -> SOURCE_SHOT_NEAREST inside shot [0,10) (6)
    frames 10,11    -> NEEDS_SPATIAL_INFERENCE (shot [10,20) has no source frame) (2)
    frames 300-305  -> NEEDS_SPATIAL_INFERENCE (shot [20,600) has no source frame) (6)
  the legacy rule fills every frame, copying the box from frame 3 across up to 303 frames (10.1 s).
"""
from __future__ import annotations

import unittest

from aic6.compose import (
    CompositionError,
    CompositionMode,
    ShotMap,
    WindowRequest,
    compose,
)
from aic6.segments import SegmentConstraint

FPS = {"0": 30.0}
N_FRAMES = {"0": 600}
BOX = [0, 0, 720]
SPATIAL = {"0": {0: BOX, 1: BOX, 2: BOX, 3: BOX}}
SHOTS = ShotMap(shots_by_video={"0": ((0, 10), (10, 20), (20, 600))})
CONSTRAINT = SegmentConstraint(0, 5)
SEGMENTS = '{"segments":[[0.0,0.2],[0.2,0.4],[10.0,10.2]]}'


def window(raw: str = SEGMENTS, *, start: float = 0.0, end: float = 11.0, index: int = 0):
    return WindowRequest(video_id="0", index=index, start_sec=start, end_sec=end, raw_output=raw)


def run(*, mode, raw=SEGMENTS, shot_map=None, allow_nearest=True, max_gap=None,
        spatial=SPATIAL, start=0.0, end=11.0):
    return compose(requests=[window(raw, start=start, end=end)], spatial_source=spatial,
                   fps_by_video=FPS, n_frames_by_video=N_FRAMES, constraint=CONSTRAINT,
                   mode=mode, shot_map=shot_map, allow_within_shot_nearest=allow_nearest,
                   max_shot_nearest_gap_frames=max_gap)


class TraceableModeTests(unittest.TestCase):
    def test_within_shot_copy_requires_a_declared_gap_limit(self):
        # no implicit unbounded copy: a shot map without a declared limit is refused.
        with self.assertRaises(CompositionError):
            run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=None)

    def test_top_level_status_and_deliverability_are_reported(self):
        report = run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=10)
        self.assertIn("status", report)
        self.assertIn("deliverable", report)
        self.assertIn("exit_code", report)

    def test_provenance_split_with_declared_shots(self):
        # declared limit 10 frames covers the within-shot distances 1..6 of frames 4..9.
        report = run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=10)
        totals = report["totals"]
        self.assertEqual(totals["frames_selected"], 18)
        self.assertEqual(totals["same_frame"], 4)
        self.assertEqual(totals["shot_nearest"], 6)
        self.assertEqual(totals["needs_spatial_inference"], 8)
        self.assertEqual(totals["resolved_frames"], 10)

    def test_gap_frames_carry_no_box_and_are_not_dropped(self):
        report = run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=10)
        frames = {f["frame"]: f for f in report["videos"][0]["frames"]}
        for frame in (10, 11, 300, 305):
            self.assertIn(frame, frames, msg="gap frames must be reported, not deleted")
            self.assertIsNone(frames[frame]["box"])
            self.assertEqual(frames[frame]["provenance"], "NEEDS_SPATIAL_INFERENCE")
        for frame in (0, 3, 4, 9):
            self.assertIsNotNone(frames[frame]["box"])

    def test_without_a_declared_shot_map_no_box_is_invented(self):
        # every frame without a same-frame source becomes NEEDS_SPATIAL_INFERENCE: 18 - 4 = 14.
        report = run(mode=CompositionMode.TRACEABLE, shot_map=None)
        self.assertEqual(report["totals"]["same_frame"], 4)
        self.assertEqual(report["totals"]["shot_nearest"], 0)
        self.assertEqual(report["totals"]["needs_spatial_inference"], 14)

    def test_declared_gap_limit_turns_far_within_shot_frames_into_gaps(self):
        # within shot [0,10): distances are 1,2,3,4,5,6 for frames 4..9; limit 3 keeps the first
        # three as nearest-box copies and makes 7,8,9 gaps.  Gaps become 3 + 2 (frames 10,11)
        # + 6 (frames 300..305) = 11.
        report = run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=3)
        self.assertEqual(report["totals"]["shot_nearest"], 3)
        self.assertEqual(report["totals"]["needs_spatial_inference"], 11)

    def test_nonpositive_declared_gap_limit_is_rejected(self):
        with self.assertRaises(CompositionError):
            run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=0)

    def test_shot_boundaries_are_respected(self):
        # frame 9 copies from within shot [0,10); frame 10 must not borrow from it.
        report = run(mode=CompositionMode.TRACEABLE, shot_map=SHOTS, max_gap=10)
        frames = {f["frame"]: f for f in report["videos"][0]["frames"]}
        self.assertEqual(frames[9]["provenance"], "SOURCE_SHOT_NEAREST")
        self.assertEqual(frames[9]["detail"]["shot"], [0, 10])
        self.assertEqual(frames[10]["provenance"], "NEEDS_SPATIAL_INFERENCE")


class ThreeStateCompositionTests(unittest.TestCase):
    def test_legal_empty_stays_empty_and_gets_no_fallback_span(self):
        report = run(mode=CompositionMode.TRACEABLE, raw='{"segments":[]}', shot_map=SHOTS, max_gap=10)
        self.assertEqual(report["totals"]["frames_selected"], 0)
        self.assertEqual(report["totals"]["empty_windows"], 1)
        self.assertEqual(report["totals"]["invalid_windows"], 0)

    def test_invalid_output_stays_invalid_and_gets_no_fallback_span(self):
        report = run(mode=CompositionMode.TRACEABLE, raw="not json at all", shot_map=SHOTS, max_gap=10)
        self.assertEqual(report["totals"]["frames_selected"], 0)
        self.assertEqual(report["totals"]["invalid_windows"], 1)
        self.assertEqual(report["totals"]["empty_windows"], 0)

    def test_legacy_mode_applies_the_historical_centred_span_only_when_asked(self):
        # legacy fallback span = 10%..90% of the 11 s window = [1.1, 9.9] s at 30 fps
        # -> round(33) .. round(297) = 33..297 inclusive = 265 frames.
        report = run(mode=CompositionMode.LEGACY_REPLAY, raw="not json at all")
        self.assertEqual(report["totals"]["frames_selected"], 265)
        self.assertTrue(report["legacy_invalid_fallback"])
        self.assertEqual(report["totals"]["invalid_windows"], 1)
        no_fallback = run(mode=CompositionMode.LEGACY_REPLAY, raw="not json at all")
        self.assertEqual(no_fallback["totals"]["frames_selected"], 265)
        explicit = compose(requests=[window("not json at all")], spatial_source=SPATIAL,
                           fps_by_video=FPS, n_frames_by_video=N_FRAMES, constraint=CONSTRAINT,
                           mode=CompositionMode.LEGACY_REPLAY, shot_map=None,
                           legacy_invalid_fallback=False)
        self.assertEqual(explicit["totals"]["frames_selected"], 0)


class LegacyReplayRuleTests(unittest.TestCase):
    def test_legacy_copies_across_a_long_distance(self):
        report = run(mode=CompositionMode.LEGACY_REPLAY)
        totals = report["totals"]
        self.assertEqual(totals["frames_selected"], 20)
        self.assertEqual(totals["legacy_nearest"], 16)
        self.assertEqual(totals["needs_spatial_inference"], 0)
        frames = {f["frame"]: f for f in report["videos"][0]["frames"]}
        # frame 305 copies the box from frame 3: a 302-frame (10.07 s) jump, exactly the
        # behaviour the new mode refuses to repeat.
        self.assertEqual(frames[305]["provenance"], "SOURCE_LEGACY_NEAREST")
        self.assertEqual(frames[305]["box"], BOX)
        self.assertEqual(frames[305]["detail"]["source_frame"], 3)
        self.assertEqual(frames[305]["detail"]["distance"], 302)
        self.assertEqual(frames[4]["detail"]["distance"], 1)
        self.assertEqual(frames[12]["detail"]["distance"], 9)

    def test_legacy_frame_selection_is_round_inclusive(self):
        report = run(mode=CompositionMode.LEGACY_REPLAY)
        frames = [f["frame"] for f in report["videos"][0]["frames"]]
        self.assertEqual(frames[:7], [0, 1, 2, 3, 4, 5, 6])
        self.assertEqual(frames[-1], 306)


class ShotMapValidationTests(unittest.TestCase):
    def test_overlapping_or_invalid_shots_are_rejected(self):
        for shots in (((0, 10), (5, 20)), ((0, 0),), ((-1, 5),)):
            with self.assertRaises(CompositionError):
                ShotMap(shots_by_video={"0": shots})

    def test_shot_of_returns_none_outside_declared_shots(self):
        self.assertIsNone(ShotMap(shots_by_video={"0": ((0, 10),)}).shot_of("0", 10))
        self.assertEqual(ShotMap(shots_by_video={"0": ((0, 10),)}).shot_of("0", 0), (0, 10))
        self.assertIsNone(ShotMap(shots_by_video={"0": ((0, 10),)}).shot_of("other", 0))


if __name__ == "__main__":
    unittest.main()
