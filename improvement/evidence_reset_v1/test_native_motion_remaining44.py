"""Two pure targeted44 checks; no imports of processor, Torch or media code."""
from copy import deepcopy
import unittest

import native_motion_remaining44 as remaining


class Checks(unittest.TestCase):
    def test_actual_bound_grid_uses_minmax_and_factor_not_raw_size_or_exact_area(self):
        calls = []
        def actual_formula(height, width, **kwargs):
            calls.append((height, width, kwargs))
            return 256, 480  # Valid32-grid area122880, not exactly131072.
        self.assertEqual(remaining.expected_grid(360, 640, actual_formula), [1, 16, 30])
        self.assertEqual(calls, [(360, 640, dict(factor=32, min_pixels=131072, max_pixels=131072))])
        with self.assertRaises(ValueError):
            remaining.expected_grid(360, 640, lambda *a, **kw: (255, 480))

    def test_reread_requires_all_nine_real_native_sha_pts_shape_rows(self):
        original = [dict(ordinal=3103 + i, original_pts_exact=str(i), normalized_pts_exact=str(i),
            rgb_shape=[360, 640, 3], pixel_sha256=str(i) * 64) for i in range(9)]
        remaining.verify_recovery_rows(deepcopy(original), original)
        changed = deepcopy(original)
        changed[4]['pixel_sha256'] = 'f' * 64
        with self.assertRaises(ValueError):
            remaining.verify_recovery_rows(changed, original)
        with self.assertRaises(ValueError):
            remaining.verify_recovery_rows(original[:3], original)


if __name__ == '__main__':
    unittest.main()
