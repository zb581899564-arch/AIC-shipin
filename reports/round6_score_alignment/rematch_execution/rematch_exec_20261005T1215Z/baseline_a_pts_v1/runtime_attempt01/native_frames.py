"""Sequential native-frame decoder; CFR keeps the unchanged OpenCV path."""
from __future__ import annotations

import math

from a_contract import sha
from pts_contract import BRANCH_NATIVE, require


class VerifiedNativeReader:
    """Decoded-order source identity, never OpenCV time/frame seeking.

    All numeric Decord starts/ends must match the integer source table exactly
    after float32 representation. Frames are consumed sequentially from zero.
    A separate spatial reopen must match the shot stage's BGR pixel SHA.
    """
    def __init__(self, source, row, clock):
        require(clock["branch"] == BRANCH_NATIVE and sha(source) == row["source_sha256"],
                "NATIVE_DECODER_SOURCE_BYTE_IDENTITY_MISMATCH")
        import decord
        import numpy as np
        self.reader = decord.VideoReader(str(source), ctx=decord.cpu(0))
        require(len(self.reader) == row["n_frames"] and
                abs(float(self.reader.get_avg_fps())-row["fps_num"]/row["fps_den"]) <=
                max(1e-6, row["fps_num"]/row["fps_den"]*1e-6), "NATIVE_DECODER_METADATA_CHANGED")
        actual = self.reader.get_frame_timestamp(list(range(row["n_frames"])))
        actual = np.asarray(actual.asnumpy() if hasattr(actual, "asnumpy") else actual)
        require(actual.shape == (row["n_frames"], 2) and str(actual.dtype) == "float32",
                "NATIVE_DECODER_CLOCK_REPRESENTATION_CHANGED")
        arrays = clock["arrays"]
        from fractions import Fraction
        tick = Fraction(arrays["raw_time_base"])
        raw = [float(t*tick) for t in arrays["native_pts_ticks"]]
        raw_ends = [float(t*tick) for t in arrays["native_frame_end_pts_ticks"]]
        origin = arrays["raw_first_pts_ticks"]*tick
        relative = [float((t-arrays["raw_first_pts_ticks"])*tick) for t in arrays["native_pts_ticks"]]
        relative_ends = [float((t-arrays["raw_first_pts_ticks"])*tick) for t in arrays["native_frame_end_pts_ticks"]]
        mode = clock["decord_clock_mode"]
        require(mode in {"RAW_CONTAINER_PTS", "SOURCE_RELATIVE_PTS", "RAW_AND_RELATIVE_EQUIVALENT_ZERO_ORIGIN"},
                "NATIVE_DECODER_CLOCK_MODE_UNCONFIRMED")
        expected = np.asarray(list(zip(raw, raw_ends)) if mode == "RAW_CONTAINER_PTS" else
                              list(zip(relative, relative_ends)), dtype=np.float32)
        require(np.array_equal(actual, expected) and np.isfinite(actual).all() and
                np.all(actual[1:, 0] > actual[:-1, 0]), "NATIVE_DECODER_ALL_FRAME_CLOCK_CHANGED")
        self.cursor, self.last_index, self.last_frame = 0, -1, None
        self.count = row["n_frames"]
        self.expected_shape = (row["height"], row["width"], 3)
        self.expected_clock_record_sha256 = clock["clock_record_sha256"]

    def read(self, index):
        require(type(index) is int and 0 <= index < self.count and index >= self.last_index,
                "NATIVE_SEQUENTIAL_FRAME_REQUEST_INVALID")
        while self.cursor <= index:
            rgb = self.reader.next().asnumpy()
            require(tuple(rgb.shape) == self.expected_shape, "NATIVE_DECODED_GEOMETRY_INVALID")
            self.last_frame = rgb[:, :, ::-1].copy()
            self.last_index = self.cursor
            self.cursor += 1
        require(self.last_index == index, "NATIVE_DECODED_ORDER_IDENTITY_MISMATCH")
        return self.last_frame


def build_native_clip(source, row, clock, plan):
    """Temporal frames use the same sequential ordinal identity as space."""
    import numpy as np
    decoder = VerifiedNativeReader(source, row, clock)
    images = [decoder.read(i)[:, :, ::-1].copy() for i in plan["source_frame_ids"]]
    array = np.stack(images)
    metadata = {"fps": row["fps_num"]/row["fps_den"],
                "frames_indices": list(plan["source_frame_ids"]),
                "total_num_frames": row["n_frames"], "video_backend": "decord"}
    return array, metadata
