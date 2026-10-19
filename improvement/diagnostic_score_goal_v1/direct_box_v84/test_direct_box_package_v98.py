import copy
from fractions import Fraction
import hashlib
import json
import tempfile
from pathlib import Path
import unittest
import direct_box_math_v84 as math84
import direct_box_package_v98 as package


class PackageTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.base=[dict(video_id=str(i),targetRatioWH=[16,9] if i%2==0 else [9,16],model_params_b=8.7,
            predictions=[dict(frame=n,bboxes=[0,0,160]) for n in range(290 if i<392 else 289)]) for i in range(426)]
        cls.source=dict(source_id='official:0:native:2',video_id='0',source_sha256='a'*64,native_ordinal=2,
            native_pts_exact='1/15',observation_index=0,baseline_box=[0,0,160],original_BASE_observed=True,
            targetRatioWH=[16,9],width=320,height=180)
        cls.clock=dict(video_id='0',source_sha256='a'*64,n_frames=290,
            normalized_exact_pts=[str(Fraction(i,30)) for i in range(290)])
        cls.boxes={cls.source['source_id']:dict(DIRECT=[80,45,160],ANCHORED_HALF=[40,22,160])}

    def patch(self,**kwargs):
        return package.patch_protected(self.base,[kwargs.get('source',self.source)],kwargs.get('boxes',self.boxes),
            arm='DIRECT',clocks={'0':kwargs.get('clock',self.clock)},legal=math84.legal_native)

    def test_exact_scope_preserves_full_times_vertical_and_original(self):
        out,changes=self.patch()
        self.assertEqual(len(changes),1);self.assertEqual(changes[0]['native_pts_exact'],'1/15')
        self.assertEqual(out[0]['predictions'][2]['bboxes'],[80,45,160])
        self.assertEqual(out[1]['predictions'],self.base[1]['predictions'])
        self.assertEqual(out[0]['predictions'][3],self.base[0]['predictions'][3])
        self.assertTrue(all(r['model_params_b']==8790237452/1e9 for r in out))
        self.assertEqual(sum(len(r['predictions']) for r in out),123506)
        self.assertEqual(self.base[0]['predictions'][2]['bboxes'],[0,0,160])

    def test_reject_wrong_pts_odd_index_and_illegal_box(self):
        for field,value in [('native_pts_exact','2/15'),('observation_index',1),('baseline_box',[1,0,160])]:
            source=dict(self.source,**{field:value})
            with self.subTest(field=field),self.assertRaises(ValueError):self.patch(source=source)
        bad=copy.deepcopy(self.boxes);bad[self.source['source_id']]['DIRECT']=[161,0,160]
        with self.assertRaises(ValueError):self.patch(boxes=bad)

    def test_zerochange_history_and_two_arm_duplicates_are_valid_stops(self):
        unchanged=copy.deepcopy(self.base)
        for r in unchanged:r['model_params_b']=package.PARAMETERS/1e9
        self.assertEqual(package.canonical(unchanged),package.canonical(self.base))
        self.assertEqual(package.disposition(unchanged,self.base,[],set(),set())[0],'STOP_ZERO_DISTINCT_BOX_CHANGE')
        changed,delta=self.patch();sha=package.canonical(changed)
        self.assertEqual(package.disposition(changed,self.base,delta,{sha},set())[0],'STOP_HISTORICAL_CANONICAL_DUPLICATE')
        self.assertEqual(package.disposition(changed,self.base,delta,set(),{sha})[0],'STOP_SAME_AS_OTHER_QUALIFIED_ARM')

    def test_canonical_matches_original_recipe_and_metadata_registry_never_opens_archives(self):
        relevant=[{k:r[k] for k in ('video_id','targetRatioWH','predictions')} for r in sorted(self.base,key=lambda r:r['video_id'])]
        expected=hashlib.sha256(json.dumps(relevant,sort_keys=True,separators=(',',':'),allow_nan=False).encode()).hexdigest()
        self.assertEqual(package.canonical(self.base),expected)
        self.assertEqual(package.history_digests(dict(canonical_sha256=[expected],linux_zip_paths=['/abs/nonexistent.zip'])),{expected})
        self.assertEqual(package.history_digests(dict(canonical_receipts={expected:['metadata only']})),{expected})

    def test_independent_decoder_uses_accepted_gpu_policy_values_not_linear_qa_roundoff(self):
        raw=[0.,0.,-.5];direct=math84.decode_native(raw,320,180);half=math84.blend_native([0,0,160],direct,320,180)
        prediction=dict(source_id=self.source['source_id'],source_sha256='a'*64,GPU_head_raw=raw,CPU_head_raw64=[.1,.1,-.1],
            native_boxes=dict(DIRECT=direct,ANCHORED_HALF=half))
        result=package.replay_boxes([self.source],[prediction],math84)
        self.assertEqual(result[self.source['source_id']]['DIRECT'],direct)
        prediction['native_boxes']['DIRECT']=[0,0,1]
        with self.assertRaises(ValueError):package.replay_boxes([self.source],[prediction],math84)

    def test_same_arm_qualification_rejects_old_status_and_unqualified_arm(self):
        common=dict(training_completion={'path':'t','sha256':'x'},adapter_weights={'path':'a','sha256':'x'},head_weights={'path':'h','sha256':'x'})
        native=dict(common,status=package.NATIVE_PASS,fixed_final_checkpoint=True,new_updates=798,total_adopted_plus_new_updates=799,
            hidden_transform='F32_L2_UNIT_VECTOR_NO_EPS',admitted_arm_names=['DIRECT','ANCHORED_HALF'],
            arms={a:dict(quality=dict(admitted=True)) for a in package.ARMS})
        reg=dict(common,admitted_arm_names=['DIRECT'],native20_quality_result={'path':'native','sha256':'x'})
        confirm=dict(native,status=package.CONFIRM_PASS,admitted_arm_names=['DIRECT'],
            native20_quality_result=reg['native20_quality_result'],frozen_admitted_arm_names=native['admitted_arm_names'])
        self.assertEqual(package.qualified_arms(native,confirm,reg),['DIRECT'])
        with self.assertRaises(ValueError):package.qualified_arms(dict(native,status='PASS_STAR_RESIZED20_PROFILE_ONLY'),confirm,reg)
        with self.assertRaises(ValueError):package.qualified_arms(native,confirm,dict(reg,admitted_arm_names=['ANCHORED_HALF']))

    def test_even_scope_uses_original_observation_index_before_selected_intersection(self):
        selected=[dict(self.source,observation_index=2)]
        odd={k:self.source[k] for k in ('video_id','source_sha256','native_ordinal','observation_index','native_pts_exact')}
        odd.update(native_ordinal=1,observation_index=1,native_pts_exact='1/30')
        even={k:selected[0][k] for k in ('video_id','source_sha256','native_ordinal','observation_index','native_pts_exact')}
        all_d=[odd,even]
        domain=dict(selection='OBS_INDEX_EVEN',protected_baseline_sha256=package.BASELINE_SHA,official_source_count=426,
            selected_D=selected,all_D=all_d,selected_D_count=1,all_D_count=2,selected_D_sha256=package.digest(selected),
            all_D_sha256=package.digest(all_d),no_nearest_or_interpolation=True,pilot_source_ids=[self.source['source_id']],
            remaining_source_ids=[],affected_video_count=1)
        package.validate_domain(domain,selected,1)
        altered=copy.deepcopy(domain);altered['selected_D'][0]['observation_index']=0
        altered['selected_D_sha256']=package.digest(altered['selected_D'])
        with self.assertRaises(ValueError):package.validate_domain(altered,altered['selected_D'],1)

    def test_provenance_retains_full_domain_and_two_old_source_types(self):
        original=[dict(video_id=r['video_id'],source_frame=p['frame'],box_xyw=p['bboxes'],legal=True,
            spatial_source='QWEN_ANCHOR_SAME_FRAME' if p['frame']%2 else 'SHOT_LINEAR_INTERPOLATION') for r in self.base for p in r['predictions']]
        _,changes=self.patch();out=package.replace_provenance(original,self.base,changes,arm='DIRECT',qa_ref={'qa':1},proof_ref={'proof':2})
        indexed={(r['video_id'],r['source_frame']):r for r in out}
        self.assertEqual(len(out),123506);self.assertEqual(indexed['0',2]['spatial_source'],package.SOURCE)
        self.assertEqual(indexed['0',3],next(r for r in original if r['video_id']=='0' and r['source_frame']==3))
        self.assertEqual({r['spatial_source'] for r in out},{'QWEN_ANCHOR_SAME_FRAME','SHOT_LINEAR_INTERPOLATION',package.SOURCE})

    def test_strict_allowlist_changes_exactly_one_expression_and_exclusive_save(self):
        old='allow={"QWEN_ANCHOR_SAME_FRAME", "SHOT_LINEAR_INTERPOLATION"}\nassert len(checks)==11\n'
        updated=package.strict_validator_text(old)
        self.assertIn(package.SOURCE,updated);self.assertTrue(updated.endswith('assert len(checks)==11\n'))
        with self.assertRaises(ValueError):package.strict_validator_text(old+old)
        with tempfile.TemporaryDirectory() as directory:
            path=Path(directory)/'new.json';package.save(path,{'ok':True})
            with self.assertRaises(FileExistsError):package.save(path,{'overwrite':True})


if __name__=='__main__':unittest.main()
