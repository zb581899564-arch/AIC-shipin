import unittest
import numpy as np
from acoustic_rank15 import pool_np,permutation,metric


class AcousticReadout(unittest.TestCase):
    def test_pool_excludes_unobserved_padding(self):
        h=np.full((1500,384),1e5,dtype=np.float32);h[2:398]=np.arange(396,dtype=np.float32)[:,None]
        f=pool_np(np,h[2:398]);self.assertTrue(np.allclose(f[:384],197.5))
        self.assertTrue(np.allclose(f[384:],np.arange(396,dtype=np.float32).std()))

    def test_wrong_valid_time_extent_rejected(self):
        with self.assertRaises(AssertionError):pool_np(np,np.zeros((400,384),dtype=np.float32))

    def test_permutation_has_no_self_and_preserves_distribution(self):
        keys={'a','b','c','d'};p=permutation(keys)
        self.assertEqual(set(p.values()),keys);self.assertTrue(all(k!=v for k,v in p.items()))
        self.assertEqual(p,permutation(reversed(sorted(keys))))

    def test_metrics_source_equal_and_target_direction(self):
        rows=[dict(source_id='a',pair_id='0',left='0',right='1',preference_left=.75),
              dict(source_id='a',pair_id='1',left='0',right='1',preference_left=.75),
              dict(source_id='b',pair_id='2',left='1',right='0',preference_left=.75)]
        result=metric(np,rows,{'0':np.array([1.]),'1':np.array([0.])},np.array([1.]))
        self.assertEqual(result['source_macro_accuracy'],.5)


if __name__=='__main__':unittest.main()
