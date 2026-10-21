import unittest
import numpy as np
import cv2
from motion_transport43 import transport, linear_control, box, normalized_center_error


class MotionTests(unittest.TestCase):
    def test_nonlinear_translation_uses_interior_pixels(self):
        rng = np.random.default_rng(43)
        image = rng.integers(0, 256, (108, 192), dtype=np.uint8)
        # Returns to its original endpoint: linear interpolation cannot see this excursion.
        displacement = [0, 1, 3, 5, 6, 5, 3, 1, 0]
        frames = np.array([cv2.warpAffine(image, np.float32([[1, 0, d], [0, 1, 0]]),
                                         (192, 108), borderMode=cv2.BORDER_REFLECT)
                           for d in displacement])
        left = right = [.5, .5]
        result = transport(frames, left, right, 192, 108)
        target = box([.5 + 6 / 192, .5], 192, 108)
        self.assertEqual(result['status'], 'BIDIRECTIONAL_NATIVE_MOTION_TRANSPORT')
        self.assertLess(normalized_center_error(result['boxes'][4], target, 108),
                        normalized_center_error(result['control_boxes'][4], target, 108))
        self.assertEqual(result['boxes'][0], box(left, 192, 108))
        self.assertEqual(result['boxes'][-1], box(right, 192, 108))

    def test_textureless_exact_fallback_and_integer_clamp(self):
        frames = np.zeros((9, 108, 192), dtype=np.uint8)
        left, right = [0., 1.], [1., 0.]
        result = transport(frames, left, right, 192, 108)
        expected = linear_control(left, right, 192, 108)
        self.assertEqual(result['status'], 'EXACT_ORIGINAL_LINEAR_FALLBACK')
        self.assertEqual(result['boxes'], expected)
        self.assertEqual(expected[0], [0, 1, 60])
        self.assertEqual(expected[-1], [132, 0, 60])
        self.assertTrue(all(b[1] in (0, 1) and b[2] == 60 for b in expected))
        # Static textured pixels must not change the old path just because
        # endpoint raw centers straddle the crop clamp boundary.
        image = np.random.default_rng(44).integers(0, 256, (108, 192), dtype=np.uint8)
        static = np.stack([image] * 9)
        left, right = [.15, .5], [.18, .5]
        result = transport(static, left, right, 1600, 900)
        self.assertEqual(result['status'], 'BIDIRECTIONAL_NATIVE_MOTION_TRANSPORT')
        self.assertEqual(result['boxes'], result['control_boxes'])


if __name__ == '__main__':
    unittest.main()
