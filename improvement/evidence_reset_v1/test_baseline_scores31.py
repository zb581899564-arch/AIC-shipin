import unittest
from baseline_scores31 import choose_native_group,validate_case,CASE_KEYS


class Tests(unittest.TestCase):
    def test_exact_tie_prefers_B_over_a_superset_but_never_over_higher_score(self):
        B={1,2,10};actions=[{1,2,3},{1,2},{1}]
        self.assertEqual(choose_native_group(actions,[0.,0.,0.],B),1)
        self.assertEqual(choose_native_group(actions,[.00001,0.,0.],B),0)
        with self.assertRaises(AssertionError):choose_native_group(actions,[float('nan'),0.,0.],B)

    def test_only_unlabelled_nonempty_suffix_model_case_schema(self):
        c={k:{}for k in CASE_KEYS};c.update(uid='S01W0',sid='S01',role='fit',answer='{"segments":[]}',suffix=[1,2])
        validate_case(c)
        for hidden in ['TP','gt','witness_F1','target_ref']:
            with self.assertRaises(AssertionError):validate_case(dict(c,**{hidden:1}))
        with self.assertRaises(AssertionError):validate_case(dict(c,suffix=[]))
        with self.assertRaises(AssertionError):validate_case(dict(c,role='optimizer_process'))


if __name__=='__main__':unittest.main()
