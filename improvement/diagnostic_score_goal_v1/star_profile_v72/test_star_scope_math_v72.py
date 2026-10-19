import unittest
import numpy as np
import crop_policy_v33 as policy
from star_scope_math_v72 import policy_predictions,evaluate,choose


def fixture(n):
    sources=[];pairs=[];values={};truth=[]
    for i in range(n):
        sid=str(i);sha=f'{i:064x}';pool=[[0,0,96],[10,10,64]]
        sources.append(dict(source_id=sid,source_sha256=sha,width=100,height=100,pool=pool,baseline_box=pool[0]))
        for j,f,r in ((0,'self','self'),(1,'f','r')):
            f=sid+f;r=sid+r;pairs.append(dict(source_id=sid,candidate_index=j,first_id=f,reverse_id=r,same_crop=j==0))
            for key,v in ((f,1. if j else 0.),(r,-1. if j else 0.)):
                values[key]=dict(source_id=sid,source_sha256=sha,CPU_value=v)
        truth.append(dict(source_id=sid,source_sha256=sha,candidate_ious=[.5,.7],reference_modified=False,baseline_index=0))
    return sources,pairs,values,truth


class Scope(unittest.TestCase):
    def test_both_scopes_fixed_gate_and_geometry_controls(self):
        for n in (19,20):
            sources,pairs,values,targets=fixture(n)
            outputs,proof=policy_predictions(sources,pairs,values,np.zeros(11),dict(RMS=np.ones(14),GEOM11_beta=np.zeros(11)),np.zeros(13),policy.geometry_features)
            result=evaluate(sources,outputs,targets,proof,policy)
            self.assertTrue(result['quality']['admitted']);self.assertAlmostEqual(result['summaries']['UTILITY']['mean_selected_iou'],.7)
    def test_missing_raw_is_failure_not_abstention(self):
        s,p,v,t=fixture(19);v.pop('0f')
        with self.assertRaises(KeyError):policy_predictions(s,p,v,np.zeros(11),dict(RMS=np.ones(14),GEOM11_beta=np.zeros(11)),np.zeros(13),policy.geometry_features)
    def test_reject_mechanism_without_visual_benefit(self):
        s,p,v,t=fixture(20)
        for x in v.values():x['CPU_value']=0.
        out,proof=policy_predictions(s,p,v,np.zeros(11),dict(RMS=np.ones(14),GEOM11_beta=np.zeros(11)),np.zeros(13),policy.geometry_features)
        result=evaluate(s,out,t,proof,policy);self.assertFalse(result['quality']['admitted'])
        self.assertEqual(choose([0.,0.,-1.]),0)


if __name__=='__main__':unittest.main()
