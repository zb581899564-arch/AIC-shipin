"""Only the new105 identity adaptation; old geometry/pixel/package tests adopted."""
import copy
from pathlib import Path
import unittest
import direct_box_scope_inputs_v106 as scope
import direct_box_inference_v107 as inference
import direct_box_package_v108 as package


def reference(name):return dict(path='/synthetic/'+name,sha256='a'*64)


def model():
    return {k:reference(k) for k in ('training_completion','adapter_weights','head_weights')}


def qualities():
    reg=dict(model(),admitted_arm_names=['DIRECT'],native20_quality_result=reference('native105'),confirm19_quality_result=reference('confirm106'))
    native=dict(model(),status='PASS_DIRECT_BOX105_NATIVE20_QUALIFIED_ARMS',fixed_final_checkpoint=True,new_updates=778,
        total_adopted_plus_new_updates=798,hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',admitted_arm_names=['DIRECT','ANCHORED_HALF'],
        arms={a:dict(quality=dict(admitted=True)) for a in package.ARMS})
    confirm=dict(native,status='PASS_DIRECT_BOX106_CONFIRM19_QUALIFIED_ARMS',admitted_arm_names=['DIRECT'],
        native20_quality_result=reg['native20_quality_result'],frozen_admitted_arm_names=native['admitted_arm_names'])
    return reg,native,confirm


def training():
    reg=dict(model(),**{k:reference(k) for k in ('frozen_GPU105_code','frozen_GPU105_registration','frozen_GPU93_code',
        'frozen_math93_code','model_config','math_code','old_TIME','old_PAIR','old_CROP')})
    original=dict(reg,schema='FROZEN_SOURCE_ONLY_DIRECT_BOX_PRECLAMP_GPU_V105',GPU_code=reg['frozen_GPU105_code'],original93_progress=reference('step19progress'))
    trained=dict(model(),status='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY',GPU_registration=reg['frozen_GPU105_registration'],
        completed_updates=778,successful_micro=3112,actual_training_forwards=3112,original_successful_updates=20,
        original_successful_forwards=88,total_adopted_plus_new_updates=798,original93_progress=original['original93_progress'],optimizer_reset=True,
        hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',adapter_reload_all288_exact=True,head_reload_all2_exact=True)
    return reg,original,trained


class IdentityTests(unittest.TestCase):
    def test_cpu_only_new105_native_and106_confirm_summaries_qualify(self):
        reg,native,confirm=qualities();native['result']=reg['native20_quality_result'];confirm['result']=reg['confirm19_quality_result']
        scope.validate_native105_summary(reg,native);scope.validate_confirm106_summary(reg,confirm)
        for status in ('PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS','PASS_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS'):
            bad=dict(native,status=status)
            with self.assertRaises(ValueError):scope.validate_native105_summary(reg,bad)
        with self.assertRaises(ValueError):scope.validate_confirm106_summary(reg,dict(confirm,status='PASS_DIRECT_BOX95_CONFIRM19_QUALIFIED_ARMS'))

    def test_106_namespace_and_reader_api_are_separate_from_old95(self):
        root=Path('/explicit/root')
        for phase in ('confirm19','formal'):
            p=scope.scope_paths(root,phase)
            self.assertEqual(p['registration'],root/('direct_box_scope_CPU_registration_106_'+phase+'.json'))
            self.assertEqual(p['output'],root/'direct_box_scope_inputs_106'/phase)
            self.assertEqual(p['remaining'],root/'direct_box_scope_remaining_admission_106_formal.json')
        self.assertEqual(scope.SCHEMA,'DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106')
        self.assertEqual(scope.GATE,'PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA')
        self.assertTrue(callable(scope.load_inputs))

    def test_107_final778_and_all88_skipped_requires_105_ancestry(self):
        reg,original,trained=training();inference.validate_training(reg,original,trained)
        for key,value in [('completed_updates',798),('successful_micro',3192),('actual_training_forwards',3111),
            ('original_successful_updates',1),('original_successful_forwards',8),('total_adopted_plus_new_updates',799),('status','COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY')]:
            with self.subTest(key=key),self.assertRaises(ValueError):inference.validate_training(reg,original,dict(trained,**{key:value}))
        bad=copy.deepcopy(original);bad['GPU_code']=reference('failed93GPU')
        with self.assertRaises(ValueError):inference.validate_training(reg,bad,trained)

    def test_reusing_93_runtime_does_not_replace_105_training_or_math_identity(self):
        reg,original,trained=training()
        for key in ('frozen_GPU93_code','frozen_math93_code','math_code'):
            bad=copy.deepcopy(reg);bad[key]=reference('different-'+key)
            with self.subTest(key=key),self.assertRaises(ValueError):inference.validate_training(bad,original,trained)
        self.assertIn('frozen_GPU105_registration',inference.GPU_REFS)
        self.assertIn('frozen_GPU93_code',inference.GPU_REFS)
        self.assertEqual(inference.STATUSES['formal'],'COMPLETE_DIRECT_BOX107_FORMAL_RAW_NOT_QUALITY')

    def test_108_same_qualified_arms_require_778_new_total798(self):
        reg,native,confirm=qualities();self.assertEqual(package.qualified_arms(native,confirm,reg),['DIRECT'])
        for key,value in [('new_updates',798),('total_adopted_plus_new_updates',799),('status','PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS')]:
            with self.subTest(key=key),self.assertRaises(ValueError):package.qualified_arms(dict(native,**{key:value}),confirm,reg)
        with self.assertRaises(ValueError):package.qualified_arms(native,confirm,dict(reg,admitted_arm_names=['ANCHORED_HALF']))

    def test_108_retains_exact_protected_identity_and_new_source_tag_only(self):
        self.assertEqual(package.BASELINE_SHA,'b37c4a2e6593fc800f54ecce2f860fee5e7d5dc74e17ce280f9ee6722afbccd3')
        self.assertEqual(package.PARAMETERS,8790237452)
        self.assertEqual(package.SCHEMA,'DIRECT_BOX105_EXACT_NATIVE_PACKAGE_V108')
        self.assertEqual(package.SOURCE,'DIRECT_BOX105_EXACT_NATIVE_OBSERVATION')
        self.assertEqual(package.FORMAL_QA,'PASS_DIRECT_BOX109_FORMAL_FIRST_RAW_HEAD_PTS_CPU_QA')
        self.assertEqual(package.canonical([dict(video_id='0',targetRatioWH=[16,9],predictions=[],model_params_b=1)]),
            package.canonical([dict(video_id='0',targetRatioWH=[16,9],predictions=[],model_params_b=9)]))


if __name__=='__main__':unittest.main()
