"""Pure decoder/loss/head-QA/arm gates; no real data or model access."""
import copy
import hashlib
from pathlib import Path
from types import SimpleNamespace
import sys
import unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parents[1]))
import crop_geometry_v31 as geometry31
import direct_box_math_v84 as math84
import direct_box_review_v84 as review


def ref(name):return dict(path='/synthetic/'+name,sha256=hashlib.sha256(name.encode()).hexdigest())


def quality_fixture(count=20):
    sources=[];targets=[];predictions=[]
    for i in range(count):
        sid='s'+str(i);sha='%064x'%i;W,H=100,70;base=[0,0,100];direct=[40,20,20]
        sources.append(dict(source_id=sid,source_sha256=sha,width=W,height=H,baseline_box=base,pool=[base],original_BASE_observed=True))
        targets.append(dict(source_id=sid,source_sha256=sha,width=W,height=H,original_reference_xywh=[20,10,60,33.75],reference_modified=False))
        predictions.append(dict(source_id=sid,source_sha256=sha,native_boxes=dict(DIRECT=direct,ANCHORED_HALF=math84.blend_native(base,direct,W,H))))
    controls={name:dict(source_ids=[s['source_id'] for s in sources],mean_iou=.35) for name in review.CONTROLS}
    return sources,targets,predictions,controls


class MathTests(unittest.TestCase):
    def test_GT_endpoint_addition_ULP_certificate_preserves_original_XYWH(self):
        reference=[123.25,12.5,float(np.nextafter(500.,np.inf))-123.25,float(np.nextafter(200.,np.inf))-12.5]
        self.assertGreater(reference[0]+reference[2],500);self.assertGreater(reference[1]+reference[3],200)
        original=copy.deepcopy(reference);actual=math84.target_xywh(reference,500,200)
        np.testing.assert_array_equal(actual,np.asarray(original,dtype=np.float64));self.assertEqual(reference,original)
        loss,_=math84.loss(torch.zeros(3),reference,500,200);self.assertTrue(torch.isfinite(loss));self.assertEqual(reference,original)

    def test_real_GT_overflow_is_rejected_and_prediction_bounds_stay_strict(self):
        for delta in (1e-10,.001):
            with self.subTest(delta=delta),self.assertRaises(ValueError):math84.target_xywh([0,0,500.+delta,100],500,200)
            with self.subTest(delta=delta),self.assertRaises(ValueError):math84.target_xywh([0,0,400,200.+delta],500,200)
        self.assertFalse(math84.legal_native([1,0,500],500,300))
        self.assertFalse(math84.legal_native([0,1,500],500,281))

    def test_zero_head_geometry_and_native_integer_bounds_and_half_down(self):
        rng=np.random.default_rng(84)
        for W,H in ((1,1),(13,3),(100,80),(17,200),(1920,1080),(3840,2161)):
            zero=math84.decode_native([0,0,0],W,H)
            self.assertEqual(zero,geometry31.candidate_pool(W,H)[0])
            for z in rng.uniform(-2,2,(20,3)):
                result=math84.decode_native(z,W,H)
                self.assertTrue(geometry31.legal(result,W,H));self.assertEqual(result,review.independent_native(z,W,H))
                actual=math84.decode_torch(torch.tensor(z,dtype=torch.float64),W,H).numpy()
                np.testing.assert_allclose(actual,math84.decode_numpy(z,W,H),rtol=0,atol=1e-10)
        self.assertEqual([math84.nearest_half_down(x) for x in (.5,1.5,2.5,-.5)],[0,1,2,-1])
        self.assertEqual(math84.blend_native([0,0,100],[40,20,20],100,70),[20,10,60])

    def test_original_non_16_9_GT_is_not_projected_or_stretched(self):
        reference=[11.,17.,40.,31.];original=copy.deepcopy(reference)
        z=torch.tensor([.01,-.02,-.4],dtype=torch.float64,requires_grad=True)
        value,parts=math84.loss(z,reference,100,80);value.backward()
        self.assertEqual(reference,original);self.assertTrue(torch.isfinite(z.grad).all());self.assertTrue(bool((z.grad!=0).all()))
        self.assertEqual(set(parts),{'smooth_l1','giou_loss','giou','total'})
        self.assertTrue(torch.isfinite(value))
        for invalid in ([-1,0,10,10],[0,0,101,10],[0,70,20,11]):
            with self.assertRaises(ValueError):math84.loss(z,invalid,100,80)

    def test_exact_match_loss_and_zero_head_initial_blocks_feature_gradient_only(self):
        zero=torch.zeros(3,dtype=torch.float64,requires_grad=True)
        value,_=math84.loss(zero,[0,11.875,100,56.25],100,80)
        self.assertAlmostEqual(float(value),0.,places=12)
        hidden=torch.linspace(-1,1,4096,requires_grad=True);weight=torch.zeros((3,4096),requires_grad=True);bias=torch.zeros(3,requires_grad=True)
        loss,_=math84.loss(torch.nn.functional.linear(hidden,weight,bias),[25,28,40,22.5],100,80);loss.backward()
        self.assertEqual(int(torch.count_nonzero(hidden.grad)),0)
        self.assertGreater(int(torch.count_nonzero(weight.grad)),0);self.assertGreater(int(torch.count_nonzero(bias.grad)),0)
        self.assertEqual(math84.PHYSICAL,math84.BASE+math84.LORA+math84.HEAD_PARAMETERS)
        self.assertEqual(math84.PIPELINE,math84.PHYSICAL+15335424+98329)


class RawAndQualityTests(unittest.TestCase):
    def raw_fixture(self):
        source=dict(source_id='s',source_sha256='a'*64,width=100,height=80,pool=[[10,20,60]],baseline_box=[10,20,60],original_BASE_observed=True)
        hidden=torch.linspace(-1,1,4096);head=dict(weight=torch.zeros((3,4096)),bias=torch.tensor([.1,-.1,-.4]))
        head['weight'][0,0]=.001;raw=head['weight']@hidden+head['bias']
        receipt=dict(**{k:source[k] for k in ('source_id','source_sha256','width','height')},adapter_weights=ref('adapter'),head_weights=ref('head'),
            decoded_xyw=math84.decode_torch(raw,100,80).tolist())
        return source,hidden,head,raw,receipt

    def test_CPU64_head_and_native_geometry_reject_corruption_and_wrong_weights(self):
        source,h,head,raw,receipt=self.raw_fixture()
        result=review.validate_raw(h,raw,receipt,head,source,adapter_weights=ref('adapter'),head_weights=ref('head'),geometry=geometry31)
        self.assertTrue(result['independent_native_geometry']);self.assertTrue(geometry31.legal(result['native_boxes']['DIRECT'],100,80))
        for change in ('raw','dtype','headref','geometry'):
            r=raw.clone();rec=copy.deepcopy(receipt)
            if change=='raw':r[0]+=.01
            elif change=='dtype':r=r.double()
            elif change=='headref':rec['head_weights']=ref('other')
            else:rec['decoded_xyw'][0]+=1
            with self.subTest(change=change),self.assertRaises(ValueError):
                review.validate_raw(h,r,rec,head,source,adapter_weights=ref('adapter'),head_weights=ref('head'),geometry=geometry31)

    def test_DIRECT_failure_remains_failure_when_pre_registered_HALF_passes(self):
        sources,targets,predictions,controls=quality_fixture()
        result=review.evaluate_scope(sources,targets,predictions,controls)
        self.assertEqual(result['admitted_arm_names'],['ANCHORED_HALF'])
        self.assertTrue(result['arms']['DIRECT']['status'].startswith('STOP_'))
        self.assertFalse(result['arms']['DIRECT']['quality']['admitted'])
        self.assertTrue(result['arms']['ANCHORED_HALF']['quality']['admitted'])
        self.assertFalse(result['pair_selfzero_applicable'])
        self.assertEqual(result['arms']['ANCHORED_HALF']['summary']['mean_selected_iou'],1.)

    def test_19_requires_frozen_arm_names_and_same_scope_controls(self):
        sources,targets,predictions,controls=quality_fixture(19)
        with self.assertRaises(ValueError):review.evaluate_scope(sources,targets,predictions,controls,scope='confirm19')
        result=review.evaluate_scope(sources,targets,predictions,controls,scope='confirm19',arm_names=['ANCHORED_HALF'])
        self.assertEqual(list(result['arms']),['ANCHORED_HALF'])
        wrong=copy.deepcopy(controls);wrong[review.CONTROLS[0]]['source_ids'].append('twentieth')
        with self.assertRaises(ValueError):review.evaluate_scope(sources,targets,predictions,wrong,scope='confirm19',arm_names=['ANCHORED_HALF'])

    def test_unique_scope_and_source_target_identity_are_not_silently_repaired(self):
        s,t,p,c=quality_fixture()
        for mode in ('source','GT','illegal'):
            sources,targets,predictions,controls=map(copy.deepcopy,(s,t,p,c))
            if mode=='source':sources[1]['source_sha256']=sources[0]['source_sha256']
            elif mode=='GT':targets[0]['reference_modified']=True
            else:predictions[0]['native_boxes']['DIRECT']=[-1,0,100]
            with self.subTest(mode=mode),self.assertRaises(ValueError):review.evaluate_scope(sources,targets,predictions,controls)

    def test_controls70_source_owned_means_are_recomputed_without_new_forward(self):
        ids=['s'+str(i) for i in range(20)];evaluation=dict(selected={},summaries={})
        for arm,value in (('UTILITY_BETA_GEOMETRY',.4),('OLD47_GEOM11',.3),('OLD33_GEOM13',.2)):
            evaluation['selected'][arm]=[dict(source_id=s,selected_iou=value) for s in ids]
            evaluation['summaries'][arm]=dict(mean_selected_iou=value)
        controls=review.controls_from_utility70(dict(evaluation=evaluation),ids)
        self.assertEqual(set(controls),set(review.CONTROLS))
        evaluation['summaries']['OLD47_GEOM11']['mean_selected_iou']=.9
        with self.assertRaises(ValueError):review.controls_from_utility70(dict(evaluation=evaluation),ids)

    def test_complete_raw_scope_binds_hidden_head_journal_before_any_target_read(self):
        source,h,head,raw,receipt=self.raw_fixture();docs={};tensors={};entries=[];sources=[];journal=[];records=[]
        for i in range(20):
            sid='s'+str(i);sha='%064x'%i;sidrow=dict(source,source_id=sid,source_sha256=sha);sources.append(sidrow)
            identifier='i'+str(i);inp=ref(identifier+'input');rec=ref(identifier+'receipt');hidden=ref(identifier+'hidden');z=ref(identifier+'rawhead')
            request=dict(id=identifier,source_id=sid,source_sha256=sha,role='screen',width=100,height=80,
                reference_or_target_in_prompt=False,input_signature={k:{'synthetic':True} for k in ('input_ids','attention_mask','pixel_values','image_grid_thw')},image_grid_thw=[[1,2,2]])
            docs[inp['path']]=request
            docs[rec['path']]=dict(receipt,id=identifier,input=inp,source_id=sid,source_sha256=sha,role='screen',model_role=review.ROLE,
                input_signature=request['input_signature'],image_grid_thw=request['image_grid_thw'],raw_hidden=hidden,raw_head=z,actual_new_forward=True,alias_of=None)
            tensors[hidden['path']]=h;tensors[z['path']]=raw
            entry=dict(id=identifier,source_id=sid,source_sha256=sha,input=inp);entries.append(entry);records.append(dict(entry,receipt=rec))
            journal += [dict(event='BEGIN_NEW_ROLE_FORWARD',id=identifier,model_role=review.ROLE,input=inp),
                dict(event='FIRST_RAW_PERSISTED',id=identifier,model_role=review.ROLE,raw_hidden=hidden,raw_head=z),
                dict(event='ACCEPTED_NEW_ROLE_RESULT',id=identifier,model_role=review.ROLE,receipt=rec,alias=False)]
        done=dict(status='COMPLETE_DIRECT_BOX20_RAW_OUTPUTS_NOT_QUALITY',model_role=review.ROLE,expected_inputs=20,sources=20,
            GPU_registration=ref('GPU84'),input_prepared=ref('prepared84'),adapter_weights=ref('adapter'),head_weights=ref('head'),
            screen_reference_read=False,entries=records,attempts=ref('attempts'),actual_forward_calls=20,aliases=0)
        def execute():return review.review_scope(done,entries,sources,head,GPU_registration=ref('GPU84'),input_prepared=ref('prepared84'),
            adapter_weights=ref('adapter'),head_weights=ref('head'),load_json=lambda r:docs[r['path']],load_tensor=lambda r:tensors[r['path']],
            geometry=geometry31,load_events=lambda r:journal)
        accepted=execute();self.assertEqual(len(accepted['predictions']),20);self.assertFalse(accepted['quality_established'])
        journal[1]['raw_head']=ref('not persisted')
        with self.assertRaises(ValueError):execute()

    def test_pilot_zero_head_gradient_phase_and_real_source_weight_loss_replay(self):
        updates=[];micros=[];schedule=[];target=dict(source_id='train',original_reference_xywh=[11,17,40,31],width=100,height=80)
        z=[.01,-.02,-.4];loss,components=math84.loss(torch.tensor(z,dtype=torch.float64),target['original_reference_xywh'],100,80)
        for micro in range(16):
            step=micro//4+1;row=dict(id='m'+str(micro),source_id='train',input_id='input',draw_weight=1.2);schedule.append(row)
            common=dict(step=step,micro=micro,id=row['id'])
            micros.extend([dict(common,event='BEGIN_TRAIN_MICRO',source_id='train'),
                dict(common,event='TRAIN_RAW_LOSS',source_id='train',input_id='input',target_xywh=target['original_reference_xywh'],
                    width=100,height=80,draw_weight=1.2,raw_head=z,unweighted_loss=float(loss),loss=1.2*float(loss),
                    components={k:float(v) for k,v in components.items()},hidden_retained_real_gradient=True),
                dict(common,event='TRAIN_BACKWARD_COMPLETE')])
        for step in range(1,5):
            groups={}
            for name in ('LoRA_A','LoRA_B','HEAD_WEIGHT','HEAD_BIAS'):
                zero=(step==1 and name.startswith('LoRA_')) or (step==2 and name=='LoRA_A')
                groups[name]=dict(tensors=144 if name.startswith('LoRA_') else 1,nonzero_tensors=0 if zero else 1,finite=True,preclip_norm=0. if zero else 1.)
            updates.append(dict(event='SUCCESSFUL_UPDATE_PERSISTED',step=step,micro=step*4,grad_groups=groups,combined_preclip_gradient_norm=1.))
        actual=review.validate_training_journals(updates,micros,schedule,dict(train=target),stage='pilot')
        self.assertTrue(actual['step1_lora_zero_expected_verified']);self.assertEqual(actual['verified_micro'],16)
        updates[1]['grad_groups']['LoRA_B']['nonzero_tensors']=0
        with self.assertRaises(ValueError):review.validate_training_journals(updates,micros,schedule,dict(train=target),stage='pilot')

    def test_complete_pilot_optimizer_checkpoint_has_all_288_matrices_and_both_head_states(self):
        torch.set_num_threads(2);adapter={};initial_adapter={}
        for layer in range(36):
            for projection,outdim in (('q_proj',4096),('k_proj',1024),('v_proj',1024),('o_proj',4096)):
                for group,shape in (('A',(8,4096)),('B',(outdim,8))):
                    key='base_model.model.language_model.layers.%d.self_attn.%s.lora_%s.weight'%(layer,projection,group)
                    adapter[key]=torch.full(shape,.002);initial_adapter[key]=torch.full(shape,.001 if group=='A' else 0.)
        head=dict(weight=torch.full((3,4096),.001),bias=torch.ones(3)*.01)
        names=[list(adapter),['head.weight','head.bias']];states={};groups=[];index=0
        for gi,group in enumerate(names):
            ids=[]
            for name in group:
                value=adapter[name] if gi==0 else head[name.split('.')[1]]
                states[index]=dict(step=torch.tensor(4.),exp_avg=torch.zeros_like(value),exp_avg_sq=torch.zeros_like(value));ids.append(index);index+=1
            groups.append(dict(params=ids,lr=[5e-5,.001][gi],betas=(.9,.999),eps=1e-8,weight_decay=0.))
        reg=dict(recipe=math84.RECIPE,prepared=ref('prepared'),train_targets=ref('train_targets'))
        initial=dict(adapter_state_dict=initial_adapter,head_state_dict=dict(weight=torch.zeros((3,4096)),bias=torch.zeros(3)))
        progress=dict(schema='DIRECT_BOX_COMPLETE_UPDATE_PROGRESS_V84',step=4,micro=16,logical_training_forwards=16,
            recipe=math84.RECIPE,no_base_tensors_saved=True,schedule_sha256='a'*64,train_schedule_reference=reg['prepared'],
            train_targets_reference=reg['train_targets'],adapter_state_dict=adapter,head_state_dict=head,
            optimizer_parameter_names_by_group=names,optimizer_parameter_names_sha256=review.digest(names),
            optimizer_state_dict=dict(state=states,param_groups=groups),torch_rng_state=torch.zeros(8,dtype=torch.uint8),
            torch_cuda_rng_state_all=[torch.zeros(8,dtype=torch.uint8)],
            numpy_rng_state=dict(name='MT19937',keys=torch.zeros(624,dtype=torch.int64),position=0,has_gauss=0,cached_gaussian=0.),python_rng_state=(3,(),None))
        inventory=dict(base=math84.BASE,direct_box_lora=math84.LORA,head=math84.HEAD_PARAMETERS,trainable=math84.LORA+math84.HEAD_PARAMETERS,
            resident=math84.PHYSICAL,pipeline=math84.PIPELINE,actual_lora_matrices=288,actual_language_targets=144,head_tensors=2,
            adapter='direct_box',original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False,
            original_TIME_counted=15335424,semantic_counted=98329)
        done=dict(status='COMPLETE_DIRECT_BOX4_ENGINEERING_NO_DEV_MODEL',GPU_registration=ref('reg84'),completed_updates=4,successful_micro=16,
            actual_training_forwards=16,actual_training_forwards_this_phase=16,recipe=math84.RECIPE,train_schedule_reference=reg['prepared'],
            train_targets_reference=reg['train_targets'],original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False,
            screen_reference_read=False,inventory=inventory,base_fingerprint=dict(parameters=math84.BASE,sha256='b'*64),schedule_sha256='a'*64,
            optimizer_parameter_names_by_group=names,optimizer_parameter_names_sha256=review.digest(names),actual_lora_A_changed=True,
            actual_lora_B_changed=True,progress=ref('progress'))
        result=review.validate_training(done,progress,initial,reg,ref('reg84'),stage='pilot',cfg=dict(expected_base_sha256='b'*64))
        self.assertEqual(result['changed_adapter_A'],144);self.assertEqual(result['changed_adapter_B'],144)
        groups[1]['params'].pop()
        with self.assertRaises(ValueError):review.validate_training(done,progress,initial,reg,ref('reg84'),stage='pilot',cfg=dict(expected_base_sha256='b'*64))


if __name__=='__main__':unittest.main()
