"""CPU checks for accepted-pixel pairing and exact native temporal mapping."""
from fractions import Fraction
import unittest

import numpy as np
import torch

if __package__:
    from .mapping import (build_native_groups, group_centers, merge_window_features,
                          pair_image_pixels, window_schedule)
else:
    from mapping import (build_native_groups, group_centers, merge_window_features,
                         pair_image_pixels, window_schedule)


def image_pixels(value, height=2, width=2, patch=16):
    # Every channel, spatial patch and pixel has a distinct value; temporal
    # duplication is the only repeated dimension in an accepted image.
    single = torch.arange(height * width * 3 * patch * patch, dtype=torch.float32)
    single = single.reshape(height * width, 3, patch, patch) + value
    return torch.stack((single, single), dim=2).reshape(height * width, 6 * patch * patch)


class PixelPairTests(unittest.TestCase):
    def test_pair_preserves_channel_spatial_and_temporal_order(self):
        frames = [image_pixels(offset) for offset in (0, 10000, 20000, 30000)]
        originals = [frame.clone() for frame in frames]
        pixels, grid = pair_image_pixels(frames, (2, 2))
        self.assertEqual(grid.tolist(), [2, 2, 2])
        self.assertEqual(grid.dtype, torch.int64)
        self.assertEqual(pixels.dtype, frames[0].dtype)
        self.assertEqual(tuple(pixels.shape), (8, 1536))
        video = pixels.reshape(2, 4, 3, 2, 16, 16)
        for pair in range(2):
            for side in range(2):
                expected = frames[2 * pair + side].reshape(4, 3, 2, 16, 16)[:, :, 0]
                self.assertTrue(torch.equal(video[pair, :, :, side], expected))
        self.assertTrue(all(torch.equal(a, b) for a, b in zip(frames, originals)))

    def test_odd_tail_only_repeats_observation_not_native_labels(self):
        frames = [image_pixels(offset) for offset in (0, 10000, 20000)]
        pixels, grid = pair_image_pixels(frames, (2, 2))
        tail = pixels[-4:].reshape(4, 3, 2, 16, 16)
        expected = frames[-1].reshape(4, 3, 2, 16, 16)[:, :, 0]
        self.assertTrue(torch.equal(tail[:, :, 0], expected))
        self.assertTrue(torch.equal(tail[:, :, 1], expected))
        self.assertEqual(grid.tolist(), [2, 2, 2])
        old = np.array([0, 0, 1, 1, 1, 2], dtype=np.int64)
        mapped = build_native_groups(old, 3)
        np.testing.assert_array_equal(mapped, [0, 0, 0, 0, 0, 1])
        self.assertEqual(len(mapped), len(old))
        np.testing.assert_array_equal(old, [0, 0, 1, 1, 1, 2])

    def test_single_observation_and_custom_patch(self):
        frame = image_pixels(7, height=1, width=2, patch=2)
        pixels, grid = pair_image_pixels([frame], (1, 2), patch_size=2)
        self.assertTrue(torch.equal(pixels, frame))
        self.assertEqual(grid.tolist(), [1, 1, 2])

    def test_nonduplicated_image_or_inconsistent_layout_is_rejected(self):
        good = image_pixels(0)
        bad = good.clone()
        bad.reshape(4, 3, 2, 16, 16)[0, 0, 1, 0, 0] += 1
        cases = [([bad], (2, 2), {}), ([good[:, :-1]], (2, 2), {}),
                 ([good, good.double()], (2, 2), {}), ([], (2, 2), {}),
                 ([good], (2, 2), {"temporal_patch": 1})]
        for frames, grid, kwargs in cases:
            with self.subTest(kwargs=kwargs, count=len(frames)):
                with self.assertRaises(ValueError):
                    pair_image_pixels(frames, grid, **kwargs)


class NativeMappingTests(unittest.TestCase):
    def test_complete_mapping_and_empty_domain(self):
        actual = build_native_groups([0, 0, 1, 2, 2, 3, 4], 5)
        np.testing.assert_array_equal(actual, [0, 0, 0, 1, 1, 1, 2])
        self.assertEqual(actual.dtype, np.int64)
        self.assertEqual(build_native_groups([], 0).shape, (0,))

    def test_missing_negative_disordered_or_noninteger_old_cells_are_rejected(self):
        for old, count in [([0, 2], 3), ([0, 1], 3), ([0, -1], 2),
                           ([0, 2, 1], 3), ([0.0, 1.0], 2), ([[0, 1]], 2),
                           ([], 1), ([0], 0)]:
            with self.subTest(old=old, count=count):
                with self.assertRaises(ValueError):
                    build_native_groups(old, count)


class WindowTests(unittest.TestCase):
    def test_fixed_starts_short_tail_and_group_overlap(self):
        self.assertEqual(window_schedule(0), [])
        self.assertEqual(window_schedule(1), [(0, 1)])
        self.assertEqual(window_schedule(64), [(0, 64)])
        self.assertEqual(window_schedule(65), [(0, 64), (32, 65)])
        self.assertEqual(window_schedule(96), [(0, 64), (32, 96)])
        self.assertEqual(window_schedule(97), [(0, 64), (32, 96), (64, 97)])
        for count in (1, 31, 64, 65, 96, 97, 128, 129):
            windows = window_schedule(count)
            covered = set()
            groups = []
            for start, end in windows:
                self.assertEqual(start % 2, 0)
                covered.update(range(start, end))
                groups.append(set(range(start // 2, (end + 1) // 2)))
            self.assertEqual(covered, set(range(count)))
            self.assertEqual(set.union(*groups), set(range((count + 1) // 2)))
            if count > 64:
                self.assertEqual(len(groups[0] & groups[1]), 16)

    def test_unaligned_or_gapped_schedule_is_rejected(self):
        for kwargs in ({"window": 63}, {"stride": 31}, {"stride": 66},
                       {"stride": 0}, {"cell_count": -1}, {"cell_count": 1.5}):
            values = {"cell_count": 100, **kwargs}
            with self.subTest(values=values):
                with self.assertRaises(ValueError):
                    window_schedule(**values)


class FeatureMergeTests(unittest.TestCase):
    def test_overlap_means_and_counts(self):
        first = np.array([[0, 10], [2, 20], [4, 40]], dtype=np.float32)
        second = np.array([[8, 80], [6, 60]], dtype=np.float32)
        means, counts = merge_window_features([([0, 1, 2], first), ([2, 3], second)], 4)
        np.testing.assert_array_equal(means, [[0, 10], [2, 20], [6, 60], [6, 60]])
        np.testing.assert_array_equal(counts, [1, 1, 2, 1])
        self.assertEqual(means.dtype, np.float32)
        self.assertEqual(counts.dtype, np.int64)
        np.testing.assert_array_equal(first, [[0, 10], [2, 20], [4, 40]])

    def test_schedule_merge_covers_odd_tail_once_without_padded_label(self):
        windows = []
        for start, end in window_schedule(97):
            ids = np.arange(start // 2, (end + 1) // 2)
            windows.append((ids, ids[:, None].astype(np.float32)))
        features, counts = merge_window_features(windows, 49)
        np.testing.assert_array_equal(features[:, 0], np.arange(49))
        np.testing.assert_array_equal(counts, [1] * 16 + [2] * 32 + [1])

    def test_missing_duplicate_nonfinite_or_inconsistent_features_are_rejected(self):
        invalid = [([([0], [[1]])], 2), ([([0, 0], [[1], [2]])], 1),
                   ([([1], [[1]])], 1), ([([0], [[np.nan]])], 1),
                   ([([0], [[np.inf]])], 1), ([([0], [[1, 2]]), ([1], [[3]])], 2),
                   ([([0, 1], [[1]])], 2), ([([0.0], [[1]])], 1), ([], 1)]
        for windows, count in invalid:
            with self.subTest(windows=windows, count=count):
                with self.assertRaises(ValueError):
                    merge_window_features(windows, count)
        features, counts = merge_window_features([], 0)
        self.assertEqual(features.shape, (0, 0))
        self.assertEqual(counts.shape, (0,))


class ExactCenterTests(unittest.TestCase):
    def test_vfr_centers_use_sampled_native_pts_exactly(self):
        pts = ["0", "1/25", "1/10", "17/50", "3/5", "11/10", "47/30"]
        samples = [0, 2, 3, 5, 6]
        expected = [Fraction(1, 20), Fraction(18, 25), Fraction(47, 30)]
        centers = group_centers(samples, pts, 0, 5)
        self.assertEqual(centers, expected)
        self.assertTrue(all(isinstance(value, Fraction) for value in centers))
        self.assertEqual(group_centers(samples, pts, 2, 5), expected[1:])
        self.assertEqual(group_centers(samples, pts, 4, 5), expected[2:])
        self.assertEqual(group_centers(samples, pts, 2, 2), [])

    def test_exact_numpy_integer_clock_and_invalid_identity(self):
        self.assertEqual(group_centers([0, 1], np.array([0, 3]), 0, 2), [Fraction(3, 2)])
        invalid = [([0, 1], [0.0, 1.0], 0, 2), ([0, 1], ["0", "1"], 1, 2),
                   ([0, 0], ["0", "1"], 0, 2), ([0, 2], ["0", "1"], 0, 2),
                   ([0, 1], ["1", "0"], 0, 2), ([0, 1], ["0", "0"], 0, 2)]
        for samples, pts, start, end in invalid:
            with self.subTest(samples=samples, pts=pts, start=start):
                with self.assertRaises(ValueError):
                    group_centers(samples, pts, start, end)


if __name__ == "__main__":
    unittest.main()
