import unittest
from fractions import Fraction as F
from intervals import expanded_windows, native_membership, overlap, duration


class BoundaryTests(unittest.TestCase):
    def test_context_clamps_to_each_original_window(self):
        windows=[dict(start_exact='0',end_exact='1',segments=[[0.9,1]]),
                 dict(start_exact='1',end_exact='2',segments=[[0,0.1]])]
        self.assertEqual(expanded_windows(windows,'1/2','1/2'),[(F(2,5),F(8,5))])
        # No padding may borrow a different window with a legal empty answer.
        self.assertEqual(expanded_windows(windows[:1],'1','1'),[(F(0),F(1))])

    def test_half_open_native_boundary_and_frozen_domain(self):
        points=[F(0),F(1,3),F(2,3),F(1)]
        self.assertEqual(native_membership(points,[(F(1,3),F(1))]),{1,2})
        self.assertEqual(native_membership(points,[(F(0),F(4,3))],(0,3)),{0,1,2})

    def test_overlap_union_does_not_double_count(self):
        a=[(0,2),(1,3)];b=[(2,4)]
        self.assertEqual(duration(a),3)
        self.assertEqual(overlap(a,b),1)

    def test_legal_empty_and_invalid_clock(self):
        self.assertEqual(expanded_windows([dict(start_exact='0',end_exact='2',segments=[])],'1','1'),[])
        self.assertEqual(native_membership([F(0),F(1)],[]),set())
        with self.assertRaises(ValueError):native_membership([F(0),F(0)],[])
        with self.assertRaises(ValueError):expanded_windows([dict(start_exact='0',end_exact='1',segments=[[0,2]])],'1','1')


if __name__ == '__main__':unittest.main()
