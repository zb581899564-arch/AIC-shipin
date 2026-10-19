import copy
import hashlib
from pathlib import Path
import sys
import unittest
import numpy as np
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_geom_promotion_v129 as promotion
import direct_box_relative_critic_v128 as frozen128


def ref(name):return dict(path='/synthetic/'+name,sha256=hashlib.sha256(name.encode()).hexdigest())


def fixture():
    models={k:ref(k) for k in ('training_completion','adapter_weights','head_weights')};evaluations={}
    for scope,n,changed,improved,gain,baseline,worst in (('native20',20,17,14,.027211,.758164,.079057),('historical19',19,15,10,.011215,.787968,.098999)):
        rows=[dict(source_id=scope+str(i),changed=i<changed,trust_changed=i<changed+3) for i in range(n)]
        summary=dict(sources=n,mean_gain=gain,mean_baseline_iou=baseline,mean_selected_iou=baseline+gain,improved=improved,worst_loss=worst,changed=changed,invalid=0)
        geom=dict(summary=summary,quality=dict(admitted=True,checks={k:True for k in promotion.ORIGINAL_CHECKS}),rows=rows)
        evaluations[scope]=dict(arms=dict(GEOM11=geom,ALWAYS_ACCEPT124=dict(summary=dict(mean_selected_iou=baseline+.027908)),JOINT=dict(quality=dict(admitted=False))))
    result=dict(status='STOP_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC',admitted_arms=[],state=ref('state'),exact_save_reload=True,
        fit=dict(fit_count=1,train_sources=602,projections=7224,rows=14448),additional_parameters=135393,pipeline_parameters=8790372845,evaluations=evaluations,**models)
    return result,models


class PromotionTests(unittest.TestCase):
    def test_geometry_score_equals_frozen_GEOM_and_ignores_PCA_hidden(self):
        rng=np.random.default_rng(129);state=dict(RMS=rng.uniform(.1,2,107),GEOM11_beta=rng.normal(size=11),
            hidden_mean=np.zeros(4096),PCA_components=np.zeros((4096,32)))
        base,proposal=[10,20,60],[20,21,40];expected=frozen128.predict_gain(state,np.ones(4096)/64,base,proposal,100,80,arm='GEOM11')
        self.assertEqual(promotion.geometry_gain(state,base,proposal,100,80),expected)
        del state['hidden_mean'];del state['PCA_components']
        self.assertEqual(promotion.geometry_gain(state,base,proposal,100,80),expected)
        self.assertEqual(promotion.geometry_gain(state,base,base,100,80),0.)
        self.assertEqual(promotion.geometry_gain(state,proposal,base,100,80),-expected)

    def test_promotion_preserves_STOP_negative_evidence_state_and_no_fit(self):
        result,models=fixture();original=copy.deepcopy(result)
        receipt=promotion.validate_promotion(result,result_ref=ref('old128'),state_ref=ref('state'),model_refs=models)
        self.assertEqual(receipt['status'],promotion.STATUS);self.assertTrue(receipt['old128_STOP_unchanged']);self.assertTrue(receipt['coefficients_not_refitted'])
        self.assertLess(receipt['negative_evidence']['native20_GEOM_minus_ALWAYS_ACCEPT124'],0.)
        self.assertFalse(receipt['fresh8_quality_established']);self.assertFalse(receipt['production_admitted']);self.assertEqual(receipt['new_fit'],0)
        self.assertEqual(receipt['development']['native20']['changed_trust_rejected'],3);self.assertEqual(result,original)

    def test_wrong_gate_state_model_or_refit_cannot_promote(self):
        result,models=fixture()
        for mode in ('old_PASS','gate','state','model','refit','negative'):
            r=copy.deepcopy(result);m=copy.deepcopy(models)
            if mode=='old_PASS':r['status']='PASS_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC'
            elif mode=='gate':r['evaluations']['historical19']['arms']['GEOM11']['quality']['checks']['minimum_gain']=False
            elif mode=='state':r['state']=ref('new_coefficients')
            elif mode=='model':m['head_weights']=ref('new_head')
            elif mode=='refit':r['fit']['fit_count']=2
            else:r['evaluations']['native20']['arms']['ALWAYS_ACCEPT124']['summary']['mean_selected_iou']=0.
            with self.subTest(mode=mode),self.assertRaises(ValueError):promotion.validate_promotion(r,result_ref=ref('old128'),state_ref=ref('state'),model_refs=m)


if __name__=='__main__':unittest.main()
