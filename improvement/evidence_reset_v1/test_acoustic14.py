import unittest
from fractions import Fraction as F
import numpy as np
from acoustic_inputs14 import verify_mapping


class NativeAudioMapping(unittest.TestCase):
    def fixture(self):
        v=np.arange(128000,dtype=np.float32)/128000
        offsets=np.array([0,64000,128000]);starts=[F(16),F(20)]
        rows=[dict(frame=i,frame_first=0,frame_stop=64000,grid_first=i*64000,
                   sub_sample_grid_residual_exact='0')for i in range(2)]
        return v,offsets,starts,rows

    def test_nonzero_native_origin(self):
        v,o,s,r=self.fixture()
        verify_mapping(np,v.copy(),np.ones(128000,bool),r,v,o,s,F(16),F(24))

    def test_wrong_sample_identity_rejected(self):
        v,o,s,r=self.fixture();w=v.copy();w[64001]+=1
        with self.assertRaises(AssertionError):verify_mapping(np,w,np.ones(128000,bool),r,v,o,s,F(16),F(24))

    def test_unobserved_not_silence(self):
        v,o,s,r=self.fixture();observed=np.ones(128000,bool);observed[100]=False
        with self.assertRaises(AssertionError):verify_mapping(np,v,observed,r,v,o,s,F(16),F(24))

    def test_changed_clock_rejected(self):
        v,o,s,r=self.fixture();s[1]+=F(1,3*16000)
        with self.assertRaises(AssertionError):verify_mapping(np,v,np.ones(128000,bool),r,v,o,s,F(16),F(24))


if __name__=='__main__':unittest.main()
