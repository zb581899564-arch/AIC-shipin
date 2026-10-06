from __future__ import annotations

import unittest
from unittest import mock

import numpy as np

from inference_recovery import reader


class FakeCapture:
    def __init__(self, frames):
        self.frames = list(frames)
        self.position = 0
        self.released = False

    def isOpened(self):
        return True

    def read(self):
        if self.position >= len(self.frames):
            return False, None
        value = self.frames[self.position]
        self.position += 1
        return True, value

    def set(self, *_args):
        raise AssertionError("non-zero seeking must never be used")

    def release(self):
        self.released = True


class ReaderTests(unittest.TestCase):
    def test_reads_from_zero_and_returns_only_requested_frames(self):
        frames = [np.full((2, 3, 3), index, dtype=np.uint8) for index in range(6)]
        capture = FakeCapture(frames)
        with mock.patch.object(reader.cv2, "VideoCapture", return_value=capture):
            actual = reader.extract_frames("unused.mp4", [5, 0, 2, 2])
        self.assertEqual(list(actual), [0, 2, 5])
        self.assertEqual([int(actual[x][0, 0, 0]) for x in actual], [0, 2, 5])
        self.assertEqual(capture.position, 6)
        self.assertTrue(capture.released)

    def test_does_not_fabricate_after_decode_failure(self):
        frames = [np.full((1, 1, 3), index, dtype=np.uint8) for index in range(3)]
        capture = FakeCapture(frames)
        with mock.patch.object(reader.cv2, "VideoCapture", return_value=capture):
            actual = reader.extract_frames("unused.mp4", [1, 4])
        self.assertEqual(set(actual), {1})

    def test_rejects_noninteger_negative_and_bool_ids(self):
        for values in ([1.5], [-1], [True]):
            with self.subTest(values=values), self.assertRaises(ValueError):
                reader.extract_frames("unused.mp4", values)


if __name__ == "__main__":
    unittest.main()
