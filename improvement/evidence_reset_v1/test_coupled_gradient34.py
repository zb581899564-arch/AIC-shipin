import unittest
import numpy as np
from coupled_gradient34_math import bounded_dot, content_metrics, decide


def row(real,shift,direction):
    r={'a':np.asarray(real,dtype=np.float64)}
    s={'a':np.asarray(shift,dtype=np.float64)}
    d={'a':np.asarray(direction,dtype=np.float32)}
    return dict(stats={
        'real_norm2':bounded_dot(r,r),'shifted_norm2':bounded_dot(s,s),'direction_norm2':bounded_dot(d,d),
        'real_dot':bounded_dot(r,d),'shifted_dot':bounded_dot(s,d),'real_shifted_dot':bounded_dot(r,s)})


class Checks(unittest.TestCase):
    def test_exact_dot_enclosed(self):
        d=bounded_dot({'x':np.array([1.,-2.])},{'x':np.array([3.,4.])})
        self.assertLessEqual(d['lower'],-5.)
        self.assertGreaterEqual(d['upper'],-5.)

    def test_pure_confidence_scale_rejected(self):
        r=row([2.,0.],[1.,0.],[1.,0.])
        m=content_metrics(r['stats'])
        self.assertLess(abs(sum(m['residual_projection_over_real_norm'])/2),1e-10)
        self.assertEqual(decide([r,r,r])['status'],'STOP_COUPLED_GRADIENT_TRANSFER_OR_SCALE_CONTROL')

    def test_positive_noncollinear_residual_and_four_denominator(self):
        r=row([1.,1.],[1.,0.],[0.,1.])
        d=decide([r,r,r])
        self.assertTrue(all(d['conditions'].values()))
        self.assertAlmostEqual(d['real_dot_macro_lower'],.75,places=10)
        self.assertEqual(d['process_denominator'],4)

    def test_zero_gradient_is_scientific_stop(self):
        r=row([0.,0.],[1.,0.],[0.,1.])
        self.assertEqual(decide([r,r,r])['status'],'STOP_ZERO_OR_NUMERICALLY_AMBIGUOUS_GRADIENT_NORM')


if __name__=='__main__':unittest.main()
