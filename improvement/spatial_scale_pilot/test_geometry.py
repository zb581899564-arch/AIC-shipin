"""Boundary and failure contracts needed before variable-width GPU inference."""
import json
import unittest
from geometry import candidates, legal, max_width, parse_choice, parse_proposal, place, iou_xyw


class GeometryContracts(unittest.TestCase):
    def test_extreme_centers_and_fractional_height(self):
        count = 0
        for W, H in [(500, 281), (1920, 1080), (1080, 1920), (169, 300), (1, 16), (16, 1)]:
            for ratio in [(16, 9), (9, 16)]:
                if H * ratio[0] // ratio[1] == 0:
                    with self.assertRaises(ValueError): max_width(W, H, ratio)
                    continue
                cw = max_width(W, H, ratio)
                for scale in (100, 85, 70, 55):
                    for center in ([0, 0], [0, 1000], [1000, 0], [1000, 1000], [501, 499]):
                        box = place(center, max(1, cw * scale // 100), W, H, ratio)
                        self.assertTrue(legal(box, W, H, ratio))
                        count += 1
        self.assertEqual(count, 220)

    def test_baseline_kept_and_no_duplicates(self):
        base = place([500, 500], 499, 500, 281, [16, 9])
        values = candidates(base, [500, 500], [500, 500], 100, 500, 281, [16, 9])
        self.assertEqual(values[0]['box'], base)
        self.assertEqual(len(values), 4)
        self.assertEqual(len({tuple(v['box']) for v in values}), len(values))
        self.assertIn('MODEL_CENTER_ORIGINAL_WIDTH', values[0]['origins'])

    def test_rejects_malformed_outputs(self):
        for raw in ['{"center":[true,500],"scale":85}', '{"center":[500.0,500],"scale":85}',
                    '{"center":[500,1001],"scale":85}', '{"center":[500,500],"scale":80}',
                    '{"center":[500,500],"scale":85,"extra":0}',
                    '{"center":[500,500],"scale":85,"scale":70}', '```json\n{}\n```']:
            with self.assertRaises((ValueError, json.JSONDecodeError)): parse_proposal(raw)
        for raw in ['{"choice":true}', '{"choice":-1}', '{"choice":6}', '{"choice":1.0}']:
            with self.assertRaises(ValueError): parse_choice(raw, 6)

    def test_ratio_math_and_iou(self):
        self.assertFalse(legal([0, 0, 169], 1920, 300, [9, 16]))
        self.assertTrue(legal([0, 0, 168], 1920, 300, [9, 16]))
        self.assertEqual(iou_xyw([10, 10, 160], [10, 10, 160, 90], [16, 9]), 1)
        self.assertEqual(iou_xyw([0, 0, 16], [100, 100, 16, 9], [16, 9]), 0)


if __name__ == '__main__':
    unittest.main()
