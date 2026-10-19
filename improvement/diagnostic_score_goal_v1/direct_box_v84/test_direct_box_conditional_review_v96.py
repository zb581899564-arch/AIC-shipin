import copy
import hashlib
import importlib.util
from pathlib import Path
import sys
import unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_conditional_review_v96 as review
import direct_box_math_recovery_v93 as math93
import direct_box_math_v84 as math84


def ref(name):return dict(path='/synthetic/'+name,sha256=hashlib.sha256(name.encode()).hexdigest())
GEOMETRY=type('Geometry',(),dict(legal=staticmethod(math84.legal_native)))


def native_quality(arms=('ANCHORED_HALF',)):
    value=dict(status=review.NATIVE_PASS,fixed_final_checkpoint=True,new_updates=798,total_adopted_plus_new_updates=799,
        hidden_transform=math93.RECIPE['hidden_transform'],admitted_arm_names=list(arms),
        training_completion=ref('trained93'),adapter_weights=ref('adapter93'),head_weights=ref('head93'),
        arms={a:dict(quality=dict(admitted=a in arms)) for a in review.ARMS})
    return value


def raw_fixture():
    reg=dict(phase='confirm19',expected_inputs=19,expected_sources=19,prepared=ref('prepared95'),CPU_registration=ref('CPU95'),
        input_acceptance=ref('gate95'),training_completion=ref('trained93'),adapter_weights=ref('adapter93'),head_weights=ref('head93'),admitted_arm_names=['ANCHORED_HALF'])
    hidden=torch.linspace(-10,10,4096);head=dict(weight=torch.zeros((3,4096)),bias=torch.tensor([.03,-.02,-.4]))
    raw=head['weight']@math93.normalize_hidden(hidden)+head['bias'];docs={};tensors={};sources=[];expected=[];records=[];events=[]
    for i in range(19):
        sid='g'+str(i);identifier='i'+str(i);sha=hashlib.sha256(sid.encode()).hexdigest()
        source=dict(source_id=sid,source_sha256=sha,width=100,height=80,pool=[[10,20,60],[20,20,40]],baseline_box=[10,20,60],original_BASE_observed=True,role='confirm');sources.append(source)
        inp=ref(identifier+'input');rec=ref(identifier+'receipt');h=ref(identifier+'hidden');z=ref(identifier+'head')
        q=dict(id=identifier,source_id=sid,source_sha256=sha,width=100,height=80,role='confirm',reference_or_target_in_prompt=False,
            input_signature={k:dict(synthetic=True) for k in ('input_ids','attention_mask','pixel_values','image_grid_thw')},image_grid_thw=[[1,2,2]])
        docs[inp['path']]=q
        receipt=dict(q,input=inp,phase='confirm19',model_role='DIRECT_BOX93_confirm19',raw_hidden=h,raw_head=z,
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],decoded_xyw=math93.decode_torch(raw,100,80).tolist(),
            actual_new_forward=True,internal_alias=False,external_alias=False,alias_of=None,
            adopted_from_acceptance=None,adopted_receipt=None,adopted_input=None,adopted_model_role=None,
            native_binding={},screen_reference_read=False,no_LM_generation=True,raw_dtype='torch.float32',hidden_dimension=4096,head_dimension=3,
            hidden_transform=math93.RECIPE['hidden_transform'],original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False)
        docs[rec['path']]=receipt;tensors[h['path']]=hidden;tensors[z['path']]=raw
        entry=dict(id=identifier,source_id=sid,source_sha256=sha,input=inp);expected.append(entry);records.append(dict(entry,receipt=rec))
        events.extend([dict(event='BEGIN_NEW_ROLE_FORWARD',id=identifier,model_role=receipt['model_role'],input=inp),
            dict(event='FIRST_RAW_PERSISTED',id=identifier,model_role=receipt['model_role'],raw_hidden=h,raw_head=z),
            dict(event='ACCEPTED_NEW_ROLE_RESULT',id=identifier,model_role=receipt['model_role'],receipt=rec,alias=False,internal_alias=False,external_alias=False)])
    done=dict(status='COMPLETE_DIRECT_BOX97_CONFIRM19_RAW_NOT_QUALITY',model_role='DIRECT_BOX93_confirm19',phase='confirm19',
        GPU_registration=ref('GPU97'),input_prepared=reg['prepared'],CPU_registration=reg['CPU_registration'],input_acceptance=reg['input_acceptance'],
        training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
        expected_inputs=19,sources=19,entries=records,attempts=ref('attempts'),actual_forward_calls=19,internal_aliases=0,aliases=0,external_adopted=0,
        admitted_arm_names=reg['admitted_arm_names'],hidden_transform=math93.RECIPE['hidden_transform'])
    return reg,head,docs,tensors,sources,expected,done,events


def execute(fixture,external=None,load_tensor=None):
    reg,head,docs,tensors,sources,expected,done,events=fixture
    return review.review_raw_scope(done,expected,sources,head,reg,registration_ref=ref('GPU97'),load_json=lambda r:docs[r['path']],
        load_tensor=load_tensor or (lambda r:tensors[r['path']]),load_events=lambda r:events,geometry=GEOMETRY,external=external or {})


class ConditionalReviewTests(unittest.TestCase):
    def test_qualified_arm_list_is_frozen_and_old84_cannot_admit93(self):
        q=native_quality();reg={k:q[k] for k in ('training_completion','adapter_weights','head_weights')}
        reg.update(phase='confirm19',admitted_arm_names=['ANCHORED_HALF'],native20_quality_result=ref('quality93'))
        self.assertEqual(review.validate_qualification(reg,q,phase='confirm19'),['ANCHORED_HALF'])
        for mode in ('old_status','arm','weight','updates'):
            a,b=copy.deepcopy(reg),copy.deepcopy(q)
            if mode=='old_status':b['status']='PASS_DIRECT_BOX84_NATIVE20_QUALIFIED_ARMS'
            elif mode=='arm':a['admitted_arm_names']=['DIRECT']
            elif mode=='weight':a['head_weights']=ref('different')
            else:b['new_updates']=800
            with self.subTest(mode=mode),self.assertRaises(ValueError):review.validate_qualification(a,b,phase='confirm19')
        q=native_quality(review.ARMS);reg.update(phase='formal',admitted_arm_names=['ANCHORED_HALF'])
        confirm=copy.deepcopy(q);confirm.update(status=review.CONFIRM_PASS,admitted_arm_names=['ANCHORED_HALF'],frozen_admitted_arm_names=list(review.ARMS),native20_quality_result=reg['native20_quality_result'])
        confirm['arms']['DIRECT']['quality']['admitted']=False
        self.assertEqual(review.validate_qualification(reg,q,phase='formal',confirm=confirm),['ANCHORED_HALF'])
        confirm['native20_quality_result']=ref('other_quality')
        with self.assertRaises(ValueError):review.validate_qualification(reg,q,phase='formal',confirm=confirm)

    def test_controls_are_computed_on_same19_from_frozen_coefficients_without_GT_selection(self):
        path=Path(__file__).resolve().parents[1]/'crop_policy_v33.py';spec=importlib.util.spec_from_file_location('_synthetic_policy33_96',path)
        policy=importlib.util.module_from_spec(spec);spec.loader.exec_module(policy)
        sources=raw_fixture()[4];targets=[dict(source_id=s['source_id'],source_sha256=s['source_sha256'],width=100,height=80,
            original_reference_xywh=[20,20,40,22.5],reference_modified=False) for s in sources]
        beta70=np.zeros(11);beta70[0]=1.;beta47=beta70.copy();beta33=np.zeros(13);beta33[1]=1.
        controls,proof=review.controls19(sources,targets,beta70=beta70,rms47=np.ones(14),beta47=beta47,beta33=beta33,geometry_features=policy.geometry_features)
        self.assertEqual(set(controls),set(review.review84.CONTROLS));self.assertTrue(all(r['mean_iou']==1. for r in controls.values()))
        self.assertEqual(proof['new_forward'],0);self.assertEqual(proof['new_fit'],0);self.assertFalse(proof['GT_used_for_geometry_choice'])
        self.assertTrue(all(r['selected_index']==1 for rows in proof['rows'].values() for r in rows))
        targets[0]['source_id']='twentieth_source'
        with self.assertRaises(ValueError):review.controls19(sources,targets,beta70=beta70,rms47=np.ones(14),beta47=beta47,beta33=beta33,geometry_features=policy.geometry_features)

    def test_raw19_L2_head_geometry_and_raw_first_journal_reject_corruption(self):
        fixture=raw_fixture();result=execute(fixture)
        self.assertEqual(result['status'],'PASS_DIRECT_BOX96_CONFIRM19_FIRST_RAW_HEAD_CPU_QA');self.assertEqual(result['actual_new_forwards'],19)
        self.assertTrue(result['predictions'][0]['raw_hidden_is_original_unnormalized'])
        fixture[-1][1]['raw_head']=ref('not_saved_first')
        with self.assertRaises(ValueError):execute(fixture)

    def test_external_successful_raw_is_adopted_by_metadata_and_never_tensor_loaded(self):
        fixture=raw_fixture();reg,head,docs,tensors,sources,expected,done,events=fixture
        current=docs[done['entries'][0]['receipt']['path']];old_input=ref('old_input');old_receipt=ref('old_receipt');qa_ref=ref('old_successful_QA')
        old_q=dict(docs[expected[0]['input']['path']],id='old0',role='screen');docs[old_input['path']]=old_q
        old_r=dict(current,id='old0',input=old_input,model_role='DIRECT_BOX93_TRAINED_screen',role='screen');docs[old_receipt['path']]=old_r
        cpu_raw=head['bias'].double().tolist()
        docs[qa_ref['path']]=dict(status='PASS_DIRECT_BOX93_SCREEN_FIRST_RAW_HEAD_NATIVE_CPU_QA',training_completion=reg['training_completion'],
            adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],predictions=[dict(id='old0',source_id=sources[0]['source_id'],source_sha256=sources[0]['source_sha256'],
                input=old_input,receipt=old_receipt,raw_hidden=current['raw_hidden'],raw_head=current['raw_head'],GPU_head_raw=cpu_raw,CPU_head_raw64=cpu_raw,
                hidden_transform=math93.RECIPE['hidden_transform'])])
        bindings=[];external=review.accepted_raw_index([qa_ref],training_completion=reg['training_completion'],adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],
            load_json=lambda r:docs[r['path']],bind=lambda r:bindings.append(r))
        current.update(actual_new_forward=False,external_alias=True,adopted_from_acceptance=qa_ref,adopted_receipt=old_receipt,adopted_input=old_input,adopted_model_role=old_r['model_role'])
        events[:3]=[dict(event='ADOPTED_PREVIOUSLY_QA_RAW',id=expected[0]['id'],model_role=current['model_role'],adopted_from_acceptance=qa_ref,
            adopted_receipt=old_receipt,adopted_input=old_input,raw_hidden=current['raw_hidden'],raw_head=current['raw_head']),
            dict(event='ACCEPTED_NEW_ROLE_RESULT',id=expected[0]['id'],model_role=current['model_role'],receipt=done['entries'][0]['receipt'],alias=True,internal_alias=False,external_alias=True)]
        done.update(actual_forward_calls=18,external_adopted=1);forbidden={current['raw_hidden']['path'],current['raw_head']['path']};loads=[]
        def tensor_load(r):
            self.assertNotIn(r['path'],forbidden);loads.append(r);return tensors[r['path']]
        result=execute(fixture,external,tensor_load);self.assertEqual(result['external_adopted'],1);self.assertEqual(len(loads),36);self.assertEqual(len(bindings),2)
        current['adopted_receipt']=ref('wrong_prior')
        with self.assertRaises(ValueError):execute(fixture,external,tensor_load)

    def test_new_raw_cannot_repeat_an_exact_previously_QAd_source_or_another_owner_raw(self):
        fixture=raw_fixture();reg,_,docs,_,sources,expected,done,_=fixture
        key=review.exact_key(docs[expected[0]['input']['path']],reg['adapter_weights'],reg['head_weights'])
        with self.assertRaises(ValueError):execute(fixture,{key:dict()})
        first=docs[done['entries'][0]['receipt']['path']];second=docs[done['entries'][1]['receipt']['path']]
        second['head_weights']=ref('old84head')
        with self.assertRaises(ValueError):execute(fixture)

    def test_complete_model_integrity_and_new798_counts_are_required(self):
        reg=dict(frozen_GPU93_registration=ref('GPU93'),training_completion=ref('trained93'),adapter_weights=ref('adapter93'),head_weights=ref('head93'))
        inventory=dict(pipeline=math93.PIPELINE,resident=math93.PHYSICAL);fingerprint=dict(parameters=math93.BASE,sha256='a'*64)
        trained=dict(status='COMPLETE_DIRECT_BOX93_NEW798_NOT_QUALITY',GPU_registration=reg['frozen_GPU93_registration'],completed_updates=798,successful_micro=3192,
            actual_training_forwards=3192,original_successful_updates=1,original_successful_forwards=8,optimizer_reset=True,hidden_transform=math93.RECIPE['hidden_transform'],
            recipe=math93.RECIPE,adapter_reload_all288_exact=True,head_reload_all2_exact=True,adapter_weights=reg['adapter_weights'],head_weights=reg['head_weights'],inventory=inventory,base_fingerprint=fingerprint)
        integrity=dict(status='PASS_DIRECT_BOX97_READONLY_MODEL_BYTE_IDENTITY',registration=ref('GPU97'),training_completion=reg['training_completion'],completion=ref('rawdone'),
            adapter_all288_exact=True,head_all2_exact=True,all_weights_frozen=True,no_training=True,targets_read=False,inventory=inventory,base_fingerprint=fingerprint)
        review.validate_model_terminal(reg,ref('GPU97'),trained,integrity,ref('rawdone'))
        integrity['all_weights_frozen']=False
        with self.assertRaises(ValueError):review.validate_model_terminal(reg,ref('GPU97'),trained,integrity,ref('rawdone'))

    def test_formal_domain_uses_even_original_indices_before_intersection(self):
        all_d=[dict(video_id='0',source_sha256='a'*64,native_ordinal=i,observation_index=i,native_pts_exact=str(i)+'/3') for i in range(64)]
        selected=[dict(d,source_id='official:0:native:'+str(d['native_ordinal'])) for d in all_d if d['observation_index']%2==0]
        domain=dict(selection='OBS_INDEX_EVEN',protected_baseline_sha256=review.BASELINE_SHA,selected_D=selected,all_D=all_d,
            selected_D_sha256=review.review84.digest(selected),all_D_sha256=review.review84.digest(all_d),selected_D_count=32,all_D_count=64,
            official_source_count=426,affected_video_count=1,pilot_source_ids=[s['source_id'] for s in selected],remaining_source_ids=[])
        reg=dict(expected_inputs=32,affected_video_count=1)
        review.validate_formal_domain(domain,selected,reg)
        domain['all_D'].append(dict(all_d[-1],native_ordinal=100,observation_index=100));domain.update(all_D_count=65,all_D_sha256=review.review84.digest(domain['all_D']))
        with self.assertRaises(ValueError):review.validate_formal_domain(domain,selected,reg)

    def test_formal_overlay_preserves_all426_times_portrait_and_D_outside_boxes(self):
        base=[dict(video_id=str(i),targetRatioWH=[9,16] if i==1 else [16,9],predictions=[dict(frame=n,bboxes=[10,20,60]) for n in range(290 if i<425 else 256)]) for i in range(426)]
        source=dict(source_id='official:0:native:2',source_sha256='a'*64,width=100,height=80,video_id='0',native_ordinal=2,native_pts_exact='2/3',observation_index=2,
            targetRatioWH=[16,9],baseline_box=[10,20,60],original_BASE_observed=True)
        prediction=dict(source_id=source['source_id'],source_sha256=source['source_sha256'],native_boxes=dict(DIRECT=[20,20,40],ANCHORED_HALF=[15,20,50]))
        clocks={'0':dict(video_id='0',source_sha256='a'*64,n_frames=290,normalized_exact_pts=[str(i)+'/3' for i in range(290)])}
        result,proof=review.exact_overlay(base,[source],[prediction],arm='ANCHORED_HALF',clocks=clocks,geometry=GEOMETRY)
        self.assertEqual(sum(len(r['predictions']) for r in result),123506);self.assertEqual(proof['changed_boxes'],1)
        self.assertEqual(result[0]['predictions'][2]['bboxes'],[15,20,50]);self.assertEqual(result[1],base[1]);self.assertEqual(result[425],base[425])
        self.assertEqual(base[0]['predictions'][2]['bboxes'],[10,20,60]);self.assertTrue(proof['all_times_preserved'])
        source['native_pts_exact']='3/4'
        with self.assertRaises(ValueError):review.exact_overlay(base,[source],[prediction],arm='DIRECT',clocks=clocks,geometry=GEOMETRY)


if __name__=='__main__':unittest.main()
