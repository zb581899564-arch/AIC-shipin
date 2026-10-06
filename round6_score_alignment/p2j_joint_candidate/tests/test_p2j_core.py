import math

import pytest

from p2j_core import (anchor_frames, box_is_legal, canonical_ratio, group_shots, interpolate_box,
                      selected_source_frames, xyw_iou)


def test_half_open_frame_mapping_and_clip_offset():
    assert selected_source_frames(10.0, 12.0, 25.0, [[0.0, 0.04], [1.0, 1.08]]) == [250, 275, 276]


def test_non_integer_fps_mapping_is_deterministic():
    frames = selected_source_frames(3.1, 4.0, 29.97, [[0.1, 0.3]])
    assert frames == list(range(math.ceil(3.1 * 29.97) + math.ceil(0.1 * 29.97),
                                math.ceil(3.1 * 29.97) + math.ceil(0.3 * 29.97)))


@pytest.mark.parametrize("segments", [[[0, 0]], [[-1, 1]], [[0, 3]], [[float("nan"), 1]], [[True, 1]]])
def test_invalid_segments_rejected(segments):
    with pytest.raises(ValueError):
        selected_source_frames(0.0, 2.0, 25.0, segments)


def test_group_shots_respects_declared_cut_and_discontinuity():
    rows = [
        {"video_id": "a", "source_frame": 1, "is_shot_start": True},
        {"video_id": "a", "source_frame": 2, "is_shot_start": False},
        {"video_id": "a", "source_frame": 3, "is_shot_start": True},
        {"video_id": "a", "source_frame": 8, "is_shot_start": False},
    ]
    assert [[x["source_frame"] for x in s] for s in group_shots(rows)] == [[1, 2], [3], [8]]


def test_duplicate_shot_frame_rejected():
    with pytest.raises(ValueError):
        group_shots([{"video_id": "a", "source_frame": 1, "is_shot_start": True}] * 2)


@pytest.mark.parametrize("gap", [True, 0, -1, 1.5])
def test_anchor_gap_must_be_positive_integer(gap):
    with pytest.raises(ValueError):
        anchor_frames([1, 2], gap)


def test_anchor_schedule_has_endpoints_and_bounded_gaps():
    anchors = anchor_frames(list(range(10, 31)), 8)
    assert anchors == [10, 18, 26, 30]
    assert max(b - a for a, b in zip(anchors, anchors[1:])) <= 8


def test_anchor_schedule_cannot_cross_missing_frame():
    with pytest.raises(ValueError):
        anchor_frames([1, 2, 4], 8)


def test_linear_interpolation_and_provenance():
    box, source = interpolate_box(5, {0: [0, 0, 10], 10: [10, 2, 10]})
    assert box == [5, 1, 10]
    assert source == {"spatial_source": "SHOT_LINEAR_INTERPOLATION", "left_anchor": 0,
                      "right_anchor": 10, "left_distance": 5, "right_distance": 5}


def test_anchor_frame_is_same_frame_provenance():
    box, source = interpolate_box(10, {10: [3, 1, 9]})
    assert box == [3, 1, 9]
    assert source["spatial_source"] == "QWEN_ANCHOR_SAME_FRAME"
    assert source["left_distance"] == source["right_distance"] == 0


def test_unbracketed_interpolation_fails_closed():
    with pytest.raises(ValueError):
        interpolate_box(4, {5: [0, 0, 10], 10: [0, 0, 10]})


def test_box_legality_and_bool_rejection():
    assert box_is_legal([10, 0, 168], 534, 300, 9, 16)
    assert not box_is_legal([True, 0, 168], 534, 300, 9, 16)
    assert not box_is_legal([400, 0, 168], 534, 300, 9, 16)


def test_iou_identity_and_disjoint():
    assert xyw_iou([1, 2, 10], [1, 2, 10]) == 1.0
    assert xyw_iou([0, 0, 10], [20, 0, 10]) == 0.0


def test_native_16_by_9_ratio_is_preserved_and_legal():
    assert canonical_ratio([16.0, 9.0]) == [16, 9]
    assert box_is_legal([0, 0, 533], 534, 300, 16, 9)


@pytest.mark.parametrize("ratio", [[0, 9], [16, True], [float("nan"), 9], [16]])
def test_invalid_target_ratio_rejected(ratio):
    with pytest.raises(ValueError):
        canonical_ratio(ratio)
