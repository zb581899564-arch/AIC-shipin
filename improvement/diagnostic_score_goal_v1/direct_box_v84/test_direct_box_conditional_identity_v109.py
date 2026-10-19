"""New105/106/107/109 identities only; does not rerun the frozen96 suite."""
import copy
import sys
from pathlib import Path
import unittest
import hashlib
import torch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_conditional_review_v109 as review
import direct_box_math_preclamp_v105 as math105
def ref(name):return dict(path='/synthetic/'+name,sha256=hashlib.sha256(name.encode()).hexdigest())
GEOMETRY=type('Geometry',(),dict(legal=staticmethod(review.math84.legal_native)))


def raw_fixture():
    reg=dict(phase='confirm19',expected_inputs=19,expected_sources=19,prepared=ref('prepared95'),CPU_registration=ref('CPU95'),
        input_acceptance=ref('gate95'),training_completion=ref('trained93'),adapter_weights=ref('adapter93'),head_weights=ref('head93'),admitted_arm_names=['ANCHORED_HALF'])
    hidden=torch.linspace(-10,10,4096);head=dict(weight=torch.zeros((3,4096)),bias=torch.tensor([.03,-.02,-.4]))
    raw=head['weight']@math105.normalize_hidden(hidden)+head['bias'];docs={};tensors={};sources=[];expected=[];records=[];events=[]
    for i in range(19):
        sid='g'+str(i);identifier='i'+str(i);sha=hashlib.sha256(sid.encode()).hexdigest()
        source=dict(source_id=sid,source_sha256=sha,width=100,height=80,pool=[[10,20,60],[20,20,40]],baseline_box=[10,20,60],original_BASE_observed=True,role='confirm');sources.append(source)
        inp=ref(identifier+'input');rec=ref(identifier+'receipt');h=ref(identifier+'hidden');z=ref(identifier+'head')
        q=dict(id=identifier,source_id=sid,source_sha256=sha,width=100,height=80,role='confirm',reference_or_target_in_prompt=False,
            input_signature={k:dict(synthetic=True) for k in ('input_ids','attention_mask','pixel_values','image_grid_thw')},image_grid_thw=[[1,2,2]])
        docs[inp['path']]=q
        receipt=dict(q,input=inp,phase='confirm19',model_role='DIRECT_BOX93_confirm19',raw_hidden=h,raw_head=z,
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],decoded_xyw=math105.decode_torch(raw,100,80).tolist(),
            actual_new_forward=True,internal_alias=False,external_alias=False,alias_of=None,
            adopted_from_acceptance=None,adopted_receipt=None,adopted_input=None,adopted_model_role=None,
            native_binding={},screen_reference_read=False,no_LM_generation=True,raw_dtype='torch.float32',hidden_dimension=4096,head_dimension=3,
            hidden_transform=math105.RECIPE['hidden_transform'],original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False)
        docs[rec['path']]=receipt;tensors[h['path']]=hidden;tensors[z['path']]=raw
        entry=dict(id=identifier,source_id=sid,source_sha256=sha,input=inp);expected.append(entry);records.append(dict(entry,receipt=rec))
        events.extend([dict(event='BEGIN_NEW_ROLE_FORWARD',id=identifier,model_role=receipt['model_role'],input=inp),
            dict(event='FIRST_RAW_PERSISTED',id=identifier,model_role=receipt['model_role'],raw_hidden=h,raw_head=z),
            dict(event='ACCEPTED_NEW_ROLE_RESULT',id=identifier,model_role=receipt['model_role'],receipt=rec,alias=False,internal_alias=False,external_alias=False)])
    done=dict(status='COMPLETE_DIRECT_BOX97_CONFIRM19_RAW_NOT_QUALITY',model_role='DIRECT_BOX93_confirm19',phase='confirm19',
        GPU_registration=ref('GPU97'),input_prepared=reg['prepared'],CPU_registration=reg['CPU_registration'],input_acceptance=reg['input_acceptance'],
        training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
        expected_inputs=19,sources=19,entries=records,attempts=ref('attempts'),actual_forward_calls=19,internal_aliases=0,aliases=0,external_adopted=0,
        admitted_arm_names=reg['admitted_arm_names'],hidden_transform=math105.RECIPE['hidden_transform'])
    return reg,head,docs,tensors,sources,expected,done,events



def current_fixture():
    replacements={old:new for old,new in (('prepared95','prepared106'),('CPU95','CPU106'),('gate95','gate106'),('GPU97','GPU107'),
        ('trained93','trained105'),('adapter93','adapter105'),('head93','head105'))}
    def convert(value):
        if isinstance(value,dict):
            for old,new in replacements.items():
                if value==ref(old):return ref(new)
            return {k:convert(v) for k,v in value.items()}
        if isinstance(value,list):return [convert(v) for v in value]
        if isinstance(value,tuple):return tuple(convert(v) for v in value)
        if value=='DIRECT_BOX93_confirm19':return 'DIRECT_BOX105_confirm19'
        if value=='COMPLETE_DIRECT_BOX97_CONFIRM19_RAW_NOT_QUALITY':return 'COMPLETE_DIRECT_BOX107_CONFIRM19_RAW_NOT_QUALITY'
        return value
    return convert(raw_fixture())


class IdentityTests(unittest.TestCase):
    def test_only_fixed105_778plus20_quality_can_freeze_109_arms(self):
        quality=dict(status=review.NATIVE_PASS,fixed_final_checkpoint=True,new_updates=778,total_adopted_plus_new_updates=798,
            hidden_transform=math105.RECIPE['hidden_transform'],training_completion=ref('trained105'),adapter_weights=ref('adapter105'),head_weights=ref('head105'),
            admitted_arm_names=['ANCHORED_HALF'],arms=dict(DIRECT=dict(quality=dict(admitted=False)),ANCHORED_HALF=dict(quality=dict(admitted=True))))
        reg={k:quality[k] for k in ('training_completion','adapter_weights','head_weights')};reg.update(phase='confirm19',admitted_arm_names=['ANCHORED_HALF'])
        self.assertEqual(review.validate_qualification(reg,quality,phase='confirm19'),['ANCHORED_HALF'])
        for key,value in (('status','PASS_DIRECT_BOX93_NATIVE20_QUALIFIED_ARMS'),('new_updates',798),('total_adopted_plus_new_updates',799)):
            wrong=copy.deepcopy(quality);wrong[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):review.validate_qualification(reg,wrong,phase='confirm19')

    def test_complete105_training_and107_integrity_are_required(self):
        reg=dict(frozen_GPU105_registration=ref('GPU105'),training_completion=ref('trained105'),adapter_weights=ref('adapter105'),head_weights=ref('head105'))
        inventory=dict(pipeline=math105.PIPELINE,resident=math105.PHYSICAL);fingerprint=dict(parameters=math105.BASE,sha256='a'*64)
        trained=dict(status='COMPLETE_DIRECT_BOX105_NEW778_NOT_QUALITY',GPU_registration=reg['frozen_GPU105_registration'],completed_updates=778,successful_micro=3112,
            actual_training_forwards=3112,original_successful_updates=20,original_successful_forwards=88,total_adopted_plus_new_updates=798,optimizer_reset=True,
            hidden_transform=math105.RECIPE['hidden_transform'],recipe=math105.RECIPE,adapter_reload_all288_exact=True,head_reload_all2_exact=True,
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],inventory=inventory,base_fingerprint=fingerprint)
        integrity=dict(status='PASS_DIRECT_BOX107_READONLY_MODEL_BYTE_IDENTITY',registration=ref('GPU107'),training_completion=reg['training_completion'],completion=ref('rawdone107'),
            adapter_all288_exact=True,head_all2_exact=True,all_weights_frozen=True,no_training=True,targets_read=False,inventory=inventory,base_fingerprint=fingerprint)
        review.validate_model_terminal(reg,ref('GPU107'),trained,integrity,ref('rawdone107'))
        for key,value in (('status','COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY'),('successful_micro',3192),('original_successful_updates',1),('original_successful_forwards',8)):
            wrong=dict(trained);wrong[key]=value
            with self.subTest(key=key),self.assertRaises(ValueError):review.validate_model_terminal(reg,ref('GPU107'),wrong,integrity,ref('rawdone107'))

    def test_only106_source_input_schema_and_gate_are_admitted(self):
        reg,_,_,_,sources,entries,_,_=current_fixture()
        reg.update(prepared_schema='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V106',input_acceptance_status='PASS_DIRECT_BOX106_SOURCE_ONLY_FIRST_CPU_QA',expected_source_ids=[s['source_id'] for s in sources])
        prepared=dict(schema=reg['prepared_schema'],phase='confirm19',inference_inputs=entries,execution_entries=entries,adopted_success={},sources=19,CPU_targets=ref('targets106'),
            **{k:reg[k] for k in ('training_completion','adapter_weights','head_weights','admitted_arm_names')})
        gate=dict(status=reg['input_acceptance_status'],phase='confirm19',prepared=reg['prepared'],registration=reg['CPU_registration'],sources=19,inputs=19,
            new_original_decode=0,old_source_processor_repeated=0,model_calls=0)
        self.assertEqual(review.validate_scope_inputs(reg,prepared,gate,dict(sources=sources))[0],entries)
        prepared['schema']='DIRECT_BOX_EXTERNAL_SOURCE_ONLY_INPUTS_V95'
        with self.assertRaises(ValueError):review.validate_scope_inputs(reg,prepared,gate,dict(sources=sources))

    def test_new107_raw_role_replays_105_L2_head_and_reports109_QA(self):
        reg,head,docs,tensors,sources,expected,done,events=current_fixture()
        def execute():return review.review_raw_scope(done,expected,sources,head,reg,registration_ref=ref('GPU107'),load_json=lambda r:docs[r['path']],
            load_tensor=lambda r:tensors[r['path']],load_events=lambda r:events,geometry=GEOMETRY,external={})
        accepted=execute();self.assertEqual(accepted['status'],'PASS_DIRECT_BOX109_CONFIRM19_FIRST_RAW_HEAD_CPU_QA')
        self.assertEqual(accepted['training_completion'],ref('trained105'));self.assertEqual(accepted['actual_new_forwards'],19)
        self.assertTrue(accepted['predictions'][0]['raw_hidden_is_original_unnormalized'])
        done['model_role']='DIRECT_BOX93_confirm19'
        with self.assertRaises(ValueError):execute()


if __name__=='__main__':unittest.main()
