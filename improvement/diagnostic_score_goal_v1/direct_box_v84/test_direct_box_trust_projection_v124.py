import copy
from fractions import Fraction
from pathlib import Path
import random
import sys
import unittest
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_trust_projection_v124 as trust


class TrustTests(unittest.TestCase):
    def test_zero_difference_and_exact_four_coordinate_fallback_preserve_baseline(self):
        base=[10,20,60];original=copy.deepcopy(base)
        result=trust.project_trust_region(base,base,100,80)
        self.assertEqual(result['box'],base);self.assertEqual(result['alpha_k'],1024);self.assertFalse(result['fallback'])
        self.assertEqual(result['certificate']['iou'],dict(numerator=1,denominator=1));self.assertEqual(base,original)
        four=[10,20,60,10.5];original=copy.deepcopy(four)
        result=trust.project_trust_region(four,[20,20,40],100,80,baseline_format='XYWH4')
        self.assertTrue(result['fallback']);self.assertEqual(result['alpha_k'],0);self.assertEqual(result['candidates_examined'],1024)
        self.assertEqual(result['box'],original);self.assertEqual(result['box4'],original);self.assertIsNone(result['box3']);self.assertEqual(four,original)
        sparse=trust.project_trust_region([0,0,1],[99999,0,1],100000,1)
        self.assertTrue(sparse['fallback']);self.assertEqual(sparse['box3'],[0,0,1]);self.assertEqual(sparse['box'],[0,0,1])

    def test_half_down_fixed_grid_and_exact_nine_tenths_boundary(self):
        exact=trust.project_trust_region([0,0,19],[1,0,19],21,11)
        self.assertEqual(exact['alpha_k'],1024);self.assertEqual(exact['certificate']['iou'],dict(numerator=9,denominator=10))
        result=trust.project_trust_region([0,0,19],[2,0,19],21,11)
        self.assertEqual(result['alpha_k'],768);self.assertEqual(result['box3'],[1,0,19])
        self.assertTrue(trust.frozen84.legal_native(result['box3'],21,11))

    def test_noninteger_original_height_is_used_without_implicit_height_substitution(self):
        base=[10,20,60,33.125]
        result=trust.project_trust_region(base,[10,20,60],100,80,baseline_format='XYWH4')
        self.assertEqual(result['box4'],[10,20,60,33.75]);self.assertEqual(result['certificate']['iou'],dict(numerator=53,denominator=54))
        self.assertEqual(base,[10,20,60,33.125])
        for gt in ([8,18,70,40],[10,20,60,33.125]):
            before=trust.exact_iou(base,gt,first_format='XYWH4',second_format='XYWH4')
            after=trust.exact_iou(result['box4'],gt,first_format='XYWH4',second_format='XYWH4')
            self.assertGreaterEqual(after,before-Fraction(1,10))
        with self.assertRaises(ValueError):trust.project_trust_region(base,[10,20,60],100,80,baseline_format='NATIVE_XYW3')
        with self.assertRaises(ValueError):trust.project_trust_region([10,20,60],[0,0,101],100,80)

    def test_synthetic_property_any_GT_bound_rounding_and_legality(self):
        rng=random.Random(124)
        for _ in range(16):
            W,H=rng.randint(20,300),rng.randint(20,200);cap=min(W,16*H//9)
            def box():
                w=rng.randint(1,cap);return [rng.randint(0,W-w),rng.randint(0,(16*H-9*w)//16),w]
            base,direct=box(),box();result=trust.project_trust_region(base,direct,W,H)
            self.assertTrue(trust.frozen84.legal_native(result['box3'],W,H))
            anchor=trust.exact_iou(result['box3'],base);self.assertGreaterEqual(anchor,Fraction(9,10))
            for _ in range(5):
                x,y=rng.randint(0,W-1),rng.randint(0,H-1);gt=[x,y,rng.randint(1,W-x),rng.randint(1,H-y)]
                before=trust.exact_iou(base,gt,second_format='XYWH4');after=trust.exact_iou(result['box3'],gt,second_format='XYWH4')
                self.assertGreaterEqual(after,before-Fraction(1,10))


if __name__=='__main__':unittest.main()
