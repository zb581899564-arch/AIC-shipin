import unittest
import numpy as np
from source_transfer23 import native_metrics


class MetricChecks(unittest.TestCase):
    def test_complete_source_counts_all_raters_not_window_average(self):
        target=dict(gt=[3,4],windows=[dict(lengths=[0,2],overlap=[[0,0],[1,2]]),
                                     dict(lengths=[1,3],overlap=[[1,1],[2,2]])])
        metrics=native_metrics(np,target,[[10.,-10.],[-10.,10.]])
        self.assertEqual(metrics['choices'],[0,1]);self.assertEqual(metrics['MAP_frames'],3)
        self.assertAlmostEqual(metrics['MAP_F1'],(4/6+4/7)/2)
        self.assertAlmostEqual(metrics['J'],metrics['MAP_F1'],places=8)

    def test_successful_empty_is_not_failure_and_ties_have_fixed_order(self):
        target=dict(gt=[0,0],windows=[dict(lengths=[0,1],overlap=[[0,0],[0,0]])])
        metrics=native_metrics(np,target,[[0.,0.]])
        self.assertEqual(metrics['choices'],[0]);self.assertEqual(metrics['MAP_F1'],1.)
        self.assertEqual(metrics['J'],.5)


if __name__=='__main__': unittest.main()
