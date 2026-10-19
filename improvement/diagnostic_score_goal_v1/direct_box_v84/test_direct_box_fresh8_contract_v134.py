import copy
import unittest
import direct_box_fresh8_contract_v134 as contract
import direct_box_fresh8_runtime_v134 as runtime


def fixture():
    models={k:dict(path='/synthetic/'+k,sha256='a'*64) for k in ('training_completion','adapter_weights','head_weights')}
    result_ref=dict(path='/synthetic/oldSTOP128',sha256='b'*64);state=dict(path='/synthetic/state',sha256='c'*64)
    result=dict(models,status=contract.DEVELOPMENT_STOP,admitted_arms=[],evaluations={})
    for scope,n in (('native20',20),('historical19',19)):
        result['evaluations'][scope]=dict(arms=dict(GEOM11=dict(summary=dict(sources=n),quality=dict(admitted=True,checks=dict(original=True)))))
    promotion=dict(models,schema='FIXED_GEOM129_POSTHOC_CONTROL_PROMOTION_ONLY',source_result=result_ref,state=state,
        arm='GEOM11',posthoc_control_promotion=True,no_refit=True)
    return models,result_ref,state,result,promotion


class NewIdentityTests(unittest.TestCase):
    def test_old128_stop_and_true_control_pass_are_required(self):
        models,r,s,q,p=fixture();contract.validate_development(p,q,result_ref=r,model_refs=models,critic_refs=dict(critic_state=s))
        with self.assertRaises(ValueError):contract.validate_development(p,dict(q,status='PASS_DIRECT_BOX128_NATIVE20_AND_HISTORICAL19_RELATIVE_CRITIC'),result_ref=r,model_refs=models,critic_refs=dict(critic_state=s))
        bad=copy.deepcopy(q);bad['evaluations']['native20']['arms']['GEOM11']['quality']['admitted']=False
        with self.assertRaises(ValueError):contract.validate_development(p,bad,result_ref=r,model_refs=models,critic_refs=dict(critic_state=s))

    def test_promotion_cannot_refit_or_change_state(self):
        models,r,s,q,p=fixture()
        with self.assertRaises(ValueError):contract.validate_development(dict(p,no_refit=False),q,result_ref=r,model_refs=models,critic_refs=dict(critic_state=s))
        with self.assertRaises(ValueError):contract.validate_development(dict(p,state=r),q,result_ref=r,model_refs=models,critic_refs=dict(critic_state=s))

    def test_new_gate_strictly_beats_always124_and_old3_without_selfcomparison(self):
        self.assertEqual(runtime.GATE['strictly_beat'],['ALWAYS124','OLD70_GEOM','OLD47_GEOM11','OLD33_GEOM13'])
        rows=[dict(source_id=str(i),baseline_iou=.5,selected_iou=.52,gain=.02,changed=i<7,true_reject=i==7,true_retain=i==0) for i in range(8)]
        controls={k:.51 for k in runtime.GATE['strictly_beat']};self.assertTrue(runtime.quality(rows,controls)[1]['admitted'])
        controls['ALWAYS124']=.53;self.assertFalse(runtime.quality(rows,controls)[1]['admitted'])
        self.assertEqual(runtime.QUALITY_PASS,'PASS_FRESH8_FIXED_GEOM129_FILE_CONFIRMATION_V134')

    def test_pure_builder_preserves_all_source_ids_and_full_parameters(self):
        refs={k:dict(path='/home/inspur/aic_video_work/existing/'+k,sha256='a'*64) for k in runtime.REG_REFS}
        refs.update(source_metadata={},CPU_max_seconds=180,CPU_max_new_bytes=100000000,GPU_max_seconds=600,review_max_seconds=120,
            deadline_utc='2026-10-18T03:22:24Z',GPU_job='new8',python='/existing/python',GPU_planned_output_bytes=10000000)
        promotion=dict(path='/home/inspur/aic_video_work/existing/promotion',sha256='b'*64)
        r=runtime.build_registration('/home/inspur/aic_video_work/newfresh8',promotion,bindings=refs)
        self.assertEqual(r['schema'],'ADMIT_FRESH8_FIXED_GEOM129_FROM_POSTHOC_CONTROL');self.assertEqual(r['arm'],'GEOM11')
        self.assertEqual(r['pipeline_parameters'],8790372845);self.assertEqual(r['sources'],contract.fixed_sources())
        self.assertEqual(sum(x['compressed_bytes']+30 for x in r['sources']),304262)


if __name__=='__main__':unittest.main()
