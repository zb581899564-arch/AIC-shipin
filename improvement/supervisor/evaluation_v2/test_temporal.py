import unittest
from evaluation_v2.temporal import intervals, score_pair, evaluate_rows, compare

class TemporalTests(unittest.TestCase):
    def test_intersection_not_envelope(self):
        self.assertEqual(score_pair([[0,2],[8,10]],[[0,10]])['f1'], 4/7)
    def test_empty_semantics(self):
        self.assertEqual(score_pair([],[])['f1'],1)
        self.assertEqual(score_pair([],[[0,1]])['f1'],0)
        self.assertEqual(score_pair([[0,1]],[])['f1'],0)
    def test_merge_no_double_count(self):
        self.assertEqual(intervals([[0,3],[2,4],[4,5]]),[[0.,5.]])
    def test_reject_bad(self):
        for pairs in [[[2,1]],[[0,float('nan')]],[[False,1]],[[0,11]]]:
            with self.assertRaises(ValueError): intervals(pairs,10)
    def test_coverage_failed_duplicate(self):
        ref=[dict(video_id='1',source_group='a',duration=10,relevant_windows=[[0,2]])]
        good=[dict(video_id='1',segments_sec=[[0,2]],status='ok')]
        self.assertEqual(evaluate_rows(good,ref)['metrics']['f1'],100)
        for bad in [[],good*2,[dict(good[0],status='failed')]]:
            with self.assertRaises(ValueError): evaluate_rows(bad,ref)
    def test_group_bootstrap(self):
        def report(value):
            return dict(metrics={'f1':value*100},rows=[dict(video_id=str(i),source_group=str(i//2),f1=value) for i in range(8)])
        result=compare(report(.6),report(.5),draws=1000)
        self.assertTrue(result['eligible_dev']); self.assertAlmostEqual(result['ci95_pp'][0],10)
        self.assertFalse(compare(report(.5),report(.5),draws=100)['eligible_dev'])

if __name__=='__main__': unittest.main()
