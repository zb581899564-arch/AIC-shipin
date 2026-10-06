"""Reliable OpenCV frame extraction without non-zero seeking."""

from __future__ import annotations

from numbers import Integral
from typing import Any, Dict, Iterable

import cv2


def extract_frames(video_path: str, frame_ids: Iterable[int]) -> Dict[int, Any]:
    """Decode from frame zero and return only explicitly requested frames.

    OpenCV's random frame seeking can land on a later decoded frame while still
    reporting success.  This reader never calls ``VideoCapture.set``.  Its frame
    counter advances exactly once for each successful ``read`` from a newly
    opened capture, so requested ids stay tied to true decode order.

    Missing or undecodable frames are omitted.  Callers must treat omissions as
    failures; this function never duplicates or fabricates pixel data.
    """

    requested = []
    for value in frame_ids:
        if isinstance(value, bool) or not isinstance(value, Integral):
            raise ValueError(f"frame id must be an integer, got {value!r}")
        frame_id = int(value)
        if frame_id < 0:
            raise ValueError(f"frame id must be non-negative, got {frame_id}")
        requested.append(frame_id)
    ids = sorted(set(requested))
    if not ids:
        return {}

    capture = cv2.VideoCapture(str(video_path))
    if not capture.isOpened():
        capture.release()
        return {}

    wanted = set(ids)
    last = ids[-1]
    decoded_index = 0
    frames: Dict[int, Any] = {}
    try:
        while decoded_index <= last:
            ok, frame = capture.read()
            if not ok:
                break
            if decoded_index in wanted:
                frames[decoded_index] = frame
            decoded_index += 1
    finally:
        capture.release()
    return frames
