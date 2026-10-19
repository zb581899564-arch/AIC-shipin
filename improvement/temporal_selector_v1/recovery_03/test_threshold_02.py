"""Read-only synthetic regression for the explicit train_v2 precision repair."""
from pathlib import Path
import sys
import unittest

import numpy as np

sys.path.insert(0,str(Path(__file__).resolve().parent))
import train_v2


def actual_coverage(probabilities,groups,threshold):
    return float(np.mean([np.mean(p[groups[sid]]>threshold) for sid,p in probabilities.items()]))


class Float32ThresholdTests(unittest.TestCase):
    def assert_actual(self,probabilities,groups,target):
        threshold,reported=train_v2.coverage_threshold(probabilities,groups,target)
        actual=actual_coverage(probabilities,groups,threshold)
        self.assertEqual(reported,actual)
        self.assertEqual(threshold,float(np.float32(threshold)))
        return threshold,reported

    def test_original_double_ulp_bug_is_reproduced(self):
        # Frozen train.py is imported, never modified or executed as a stage.
        import train as original
        probabilities={'s':np.array([.8,.2],dtype=np.float32)}
        groups={'s':np.array([0,1],dtype=np.int64)}
        threshold,reported=original.coverage_threshold(probabilities,groups,.5)
        self.assertEqual(reported,.5)
        self.assertEqual(actual_coverage(probabilities,groups,threshold),0.)
        fixed,coverage=self.assert_actual(probabilities,groups,.5)
        self.assertEqual(coverage,.5)
        self.assertEqual(fixed,float(np.nextafter(np.float32(.8),np.float32(-np.inf))))

    def test_ties_are_selected_as_one_boundary(self):
        probabilities={'s':np.array([.8,.8,.2],dtype=np.float32)}
        groups={'s':np.array([0,1,2],dtype=np.int64)}
        threshold,coverage=self.assert_actual(probabilities,groups,2/3)
        self.assertAlmostEqual(coverage,2/3)
        np.testing.assert_array_equal(probabilities['s']>threshold,[True,True,False])
        # Equidistant coverage choices retain the registered higher-cutoff tie rule.
        threshold,coverage=self.assert_actual({'s':np.array([.5,.5],dtype=np.float32)},
                                            {'s':np.array([0,1],dtype=np.int64)},.5)
        self.assertEqual(coverage,0.)

    def test_exact_zero_one_probabilities_and_coverage_endpoints(self):
        probabilities={'s':np.array([1.,0.],dtype=np.float32)}
        groups={'s':np.array([0,1],dtype=np.int64)}
        for target in (0.,.5,1.):
            _,coverage=self.assert_actual(probabilities,groups,target)
            self.assertEqual(coverage,target)

    def test_actual_native_duration_and_equal_source_weights(self):
        probabilities={'a':np.array([.9,.4],dtype=np.float32),
                       'b':np.array([.7,.2],dtype=np.float32)}
        # Source a contributes .75/2 at .9; source b contributes .25/2 at .7.
        # Its longer native axis must not give source b more total weight.
        groups={'a':np.array([0,0,0,1],dtype=np.int64),
                'b':np.array([0]*25+[1]*75,dtype=np.int64)}
        threshold,coverage=self.assert_actual(probabilities,groups,.5)
        self.assertEqual(coverage,.5)
        self.assertEqual(float((probabilities['a'][groups['a']]>threshold).mean()),.75)
        self.assertEqual(float((probabilities['b'][groups['b']]>threshold).mean()),.25)
        pooled=(3+25)/(4+100)
        self.assertNotAlmostEqual(coverage,pooled)

    def test_all_tied_zero_or_one_outputs_keep_mask_consistency(self):
        for value in (0.,1.):
            probabilities={'s':np.full(3,value,dtype=np.float32)}
            groups={'s':np.array([0,0,1,2],dtype=np.int64)}
            for target in (0.,.4,.6,1.):
                _,coverage=self.assert_actual(probabilities,groups,target)
                self.assertIn(coverage,(0.,1.))


if __name__=='__main__':
    unittest.main(verbosity=2)
