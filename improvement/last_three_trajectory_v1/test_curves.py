"""Small meaningful checks for the new interpolation and isolation risks."""
import unittest
from curves import pchip_slopes, sample_curve, ShotTrajectory, groups


class CurveTests(unittest.TestCase):
    def test_linear_native_time_reproduction(self):
        t, y = [0., .2, .9, 2.], [0., 2., 9., 20.]
        slopes = pchip_slopes(t, y)
        for x in [0., .1, .2, .5, 1.5, 2.]:
            self.assertAlmostEqual(sample_curve(t, y, slopes, x), 10*x)

    def test_no_overshoot_at_reversal(self):
        t, y = [0., 1., 2., 3.], [0., 100., 0., 20.]
        slopes = pchip_slopes(t, y)
        for i in range(3):
            for j in range(101):
                value = sample_curve(t, y, slopes, i+j/100)
                self.assertTrue(min(y[i:i+2])-1e-8 <= value <= max(y[i:i+2])+1e-8)

    def test_native_knot_identity(self):
        t, y = [0., .13, 1.2], [1., 40., 3.]
        for x, expected in zip(t, y):
            self.assertAlmostEqual(sample_curve(t, y, pchip_slopes(t, y), x), expected)

    def test_degenerate_short_shot_and_width(self):
        trajectory = ShotTrajectory([4], {4: {'box_xyw': [8, 9, 16]}}, {4: 1.})
        source = dict(width=100, height=100, targetRatioWH=[16,9])
        for policy in ('pchip','median3','shot_representative'):
            self.assertEqual(trajectory.sample(policy,4,1.,[8,9,16],source),[8,9,16])

    def test_scene_or_missing_frame_splits(self):
        rows = [dict(video_id='0',source_frame=f,is_shot_start=f==3) for f in [0,1,3,4,7]]
        self.assertEqual([[r['source_frame'] for r in s] for s in groups(rows)], [[0,1],[3,4],[7]])

    def test_duplicate_native_knots_rejected(self):
        with self.assertRaises(ValueError):
            pchip_slopes([0.,0.],[2.,3.])


if __name__ == '__main__':
    unittest.main()
