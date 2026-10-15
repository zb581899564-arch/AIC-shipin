import unittest
from fractions import Fraction as F
from contract_v2 import native_ranges, project_context


class ProspectiveContractTests(unittest.TestCase):
    def test_excess_intersection_stops(self):
        candidates = [[0,3],[4,7],[8,11],[12,15],[16,19]]
        proposal = [[1,5],[6,9],[10,13],[14,17],[18,20]]
        with self.assertRaisesRegex(ValueError, 'exceeds five'):
            project_context(proposal,candidates,F(0),F(30),[str(i) for i in range(31)],F(0))

    def test_exact_source_offset_once(self):
        result, detail = project_context([[3,7]], [[4,9]], F(1), F(30),
            [str(i) for i in range(90,121)],F(90))
        self.assertEqual(result,[[4.0,8.0]])
        self.assertEqual(detail['native_ranges'],[[4,8]])
        self.assertEqual(detail['exact_final'],[['4','8']])

    def test_interval_between_frames_rejected(self):
        with self.assertRaisesRegex(ValueError,'no real native'):
            native_ranges([[.1,.2]],['0','1/3','2/3'],F(0))

    def test_empty_remains_legitimate_empty(self):
        result, detail = project_context([],[[0,1]],F(0),F(30),['0','1'],F(0))
        self.assertEqual(result,[])
        self.assertEqual(detail['native_ranges'],[])


if __name__ == '__main__':
    unittest.main()
