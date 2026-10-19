import unittest
import numpy as np
import torch
from roi_ridge import fit_projection,fit_coefficients,predict,choose,ARMS
from roi_pool import FEATURE_DIM,VISUAL_DIM


class RelativeRidgeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        torch.set_num_threads(2)
        rng=np.random.default_rng(12)
        cls.sources={str(i):dict(features=rng.normal(size=(9,FEATURE_DIM)).astype(np.float32),
                               targets=rng.uniform(size=9)) for i in range(5)}
        cls.norm=dict(mean=np.zeros(FEATURE_DIM,np.float32),std=np.ones(FEATURE_DIM,np.float32))
        cls.state,cls.x,cls.y,cls.w,cls.rows=fit_projection(cls.sources,list(cls.sources),cls.norm,synthetic=True)

    def test_train_only_projection_and_exactzero_origins(self):
        self.assertEqual(self.state['PCA'].shape,(VISUAL_DIM,32))
        for _,start,end in self.rows:
            np.testing.assert_array_equal(self.x[start],np.zeros(40))
            self.assertEqual(self.y[start],0.)
            self.assertEqual(self.w[start],0.)
            self.assertAlmostEqual(self.w[start:end].sum(),.2)

    def test_weighted_ridge_normal_equations_and_geometry_zero(self):
        for arm in ARMS:
            b,r=fit_coefficients(self.x,self.y,self.w,arm)
            x=self.x.copy()
            if arm==ARMS[1]:x[:,:32]=0
            gradient=x.T@(self.w*(x@b-self.y))+.01*b
            np.testing.assert_allclose(gradient,np.zeros(40),atol=1e-10)
            if arm==ARMS[1]:np.testing.assert_array_equal(b[:32],np.zeros(32))
            self.assertEqual(r['optimizer_updates'],0)

    def test_query_delta_origin_and_save_reload_bit_equal(self):
        b,_=fit_coefficients(self.x,self.y,self.w,ARMS[0])
        before=predict(self.state,b,self.sources['0']['features'],ARMS[0])
        after=predict({k:v.copy() if isinstance(v,np.ndarray) else v for k,v in self.state.items()},b.copy(),self.sources['0']['features'],ARMS[0])
        np.testing.assert_array_equal(before,after);self.assertEqual(before[0],0.)
        self.assertEqual(choose(np.array([0.,-1.,0.])),0)
        self.assertEqual(choose(np.array([0.,.1,.1])),1)

    def test_actual_fit_and_query_use_same_relative_coordinates(self):
        for arm in ARMS:
            b,_=fit_coefficients(self.x,self.y,self.w,arm)
            x=self.x.copy()
            if arm==ARMS[1]:x[:,:32]=0
            for sid,start,end in self.rows:
                query=predict(self.state,b,self.sources[sid]['features'],arm)
                np.testing.assert_allclose(query,x[start:end]@b,atol=1e-12,rtol=1e-12)

    def test_actual_recipe_rejects_synthetic_source_count(self):
        with self.assertRaises(ValueError):fit_projection(self.sources,list(self.sources),self.norm)


if __name__=='__main__':unittest.main()
