import copy
from pathlib import Path
import random
import sys
import tempfile
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_relative_critic_v128 as critic
import direct_box_trust_projection_v124 as frozen124


class CriticTests(unittest.TestCase):
    def test_integer_vectorized_projection_matches_frozen124_edges_and_random(self):
        cases=[([0,0,19],[2,0,19],21,11),([0,0,1],[99999,0,1],100000,1),([10,20,60],[10,20,60],100,80),([0,0,1],[1,1,1],2,2)]
        rng=random.Random(128)
        for _ in range(12):
            W,H=rng.randint(10,600),rng.randint(10,500);cap=min(W,16*H//9)
            def box():
                w=rng.randint(1,cap);return [rng.randint(0,W-w),rng.randint(0,(16*H-9*w)//16),w]
            cases.append((box(),box(),W,H))
        for base,direct,W,H in cases:
            expected=frozen124.project_trust_region(base,direct,W,H);actual=critic.trust_project_native3(base,direct,W,H)
            self.assertEqual(actual['box3'],expected['box3']);self.assertEqual(actual['alpha_k'],expected['alpha_k']);self.assertEqual(actual['fallback'],expected['fallback'])

    def test_exact_geometry11_selfzero_antisymmetry_and_no_independent_hidden(self):
        base=[10,20,60];proposal=[20,21,40];pc=np.linspace(-1,1,32)
        g=critic.geometry11(base,100,80);x,y,w,h=.1,.25,.6,9*60/(16*80)
        np.testing.assert_array_equal(g,np.array([x,y,w,h,x*x,y*y,w*w,h*h,x*y,x*w,y*h]))
        forward=critic.relative_features(pc,base,proposal,100,80);reverse=critic.relative_features(pc,proposal,base,100,80)
        self.assertEqual(forward.shape,(107,));np.testing.assert_array_equal(reverse,-forward)
        np.testing.assert_array_equal(critic.relative_features(pc,base,base,100,80),np.zeros(107))
        np.testing.assert_array_equal(forward[:11],critic.geometry11(proposal,100,80)-g)

    def test_train_only_centered_PCA32_sign_and_exact_state_reload(self):
        rng=np.random.default_rng(128);hidden=rng.normal(size=(40,4096)).astype(np.float32);hidden/=np.linalg.norm(hidden,axis=1)[:,None]
        mean,components,report=critic.fit_pca(hidden)
        np.testing.assert_array_equal(mean,hidden.astype(np.float64).mean(axis=0));np.testing.assert_allclose(components.T@components,np.eye(32),atol=1e-7,rtol=0)
        self.assertTrue(all(components[np.argmax(np.abs(components[:,i])),i]>0 for i in range(32)));self.assertEqual(report['development_rows_used'],0)
        state=dict(hidden_mean=mean,PCA_components=components,RMS=np.ones(107),JOINT_beta=np.ones(107),GEOM11_beta=np.ones(11))
        self.assertEqual(sum(a.size for a in state.values()),135393)
        with tempfile.TemporaryDirectory() as d:
            loaded=critic.save_reload_state(Path(d)/'state.npz',state)
            for key in state:np.testing.assert_array_equal(loaded[key],state[key])
        self.assertEqual(critic.predict_gain(state,hidden[0],[10,20,60],[10,20,60],100,80),0.)

    def test_ridge_is_sum_source_mean24_SSE_plus_one_and_GEOM_uses_same_scale(self):
        rng=np.random.default_rng(126);positive=rng.normal(size=(3,12,107));features=np.concatenate((positive,-positive),axis=1)
        features[:,:,106]=0.;gains=rng.normal(scale=.03,size=(3,24))
        rms,joint,geom,_=critic.fit_ridge(features,gains);x=(features/rms).reshape(-1,107);y=gains.reshape(-1)
        self.assertEqual(rms[106],1.)
        np.testing.assert_allclose(joint,np.linalg.solve(x.T@x/24+np.eye(107),x.T@y/24),rtol=0,atol=1e-12)
        np.testing.assert_allclose(geom,np.linalg.solve(x[:,:11].T@x[:,:11]/24+np.eye(11),x[:,:11].T@y/24),rtol=0,atol=1e-12)
        averaged=np.linalg.solve(x.T@x/72+np.eye(107),x.T@y/72)
        self.assertGreater(float(np.linalg.norm(joint-averaged)),1e-5)


if __name__=='__main__':unittest.main()
