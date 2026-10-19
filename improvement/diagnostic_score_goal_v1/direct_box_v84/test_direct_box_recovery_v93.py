import copy
import hashlib
import sys
from pathlib import Path
import unittest
import numpy as np
import torch
sys.path.insert(0,str(Path(__file__).resolve().parent))
import direct_box_math_v84 as math84
import direct_box_math_recovery_v93 as math93
import direct_box_review_recovery_v93 as review


def ref(name):return dict(path='/synthetic/'+name,sha256=hashlib.sha256(name.encode()).hexdigest())


def warm_fixture(full=False):
    adapter={}
    for layer in range(36):
        for projection,outdim in (('q_proj',4096),('k_proj',1024),('v_proj',1024),('o_proj',4096)):
            for group,shape in (('A',(8,4096)),('B',(outdim,8))):
                name='base_model.model.language_model.layers.%d.self_attn.%s.lora_%s.weight'%(layer,projection,group)
                adapter[name]=torch.full(shape if full else (1,),.001 if group=='A' else 0.)
    head=dict(weight=torch.full((3,4096),.001),bias=torch.full((3,),.001))
    rng=dict(torch_rng_state=torch.arange(8,dtype=torch.uint8),torch_cuda_rng_state_all=[torch.arange(8,dtype=torch.uint8)],
        numpy_rng_state=dict(name='MT19937',keys=torch.zeros(624,dtype=torch.int64),position=0,has_gauss=0,cached_gaussian=0.),python_rng_state=(3,(),None))
    original=dict(schema='DIRECT_BOX_COMPLETE_UPDATE_PROGRESS_V84',step=1,micro=4,logical_training_forwards=4,
        recipe=math84.RECIPE,adapter_state_dict=adapter,head_state_dict=head,**rng)
    initial=copy.deepcopy(original);initial['optimizer_state_dict']=dict(state={},param_groups=[dict(params=list(range(288))),dict(params=[288,289])])
    return original,initial


class RecoveryTests(unittest.TestCase):
    def test_L2_F32_preserves_gradient_and_eliminates_unscaled_head_saturation(self):
        hidden=torch.full((4096,),100.,requires_grad=True);head=torch.full((3,4096),.001)
        unscaled=head@hidden;normalized=math93.normalize_hidden(hidden);scaled=head@normalized
        self.assertEqual(normalized.dtype,torch.float32);self.assertAlmostEqual(float(torch.linalg.vector_norm(normalized)),1.,places=6)
        self.assertGreater(float(unscaled[0]),400.);self.assertLess(float(scaled[0]),.065)
        weights=torch.zeros((3,4096),requires_grad=True);weights.data[0,0]=.1
        (weights@normalized).sum().backward();self.assertGreater(int(torch.count_nonzero(hidden.grad)),0)
        for invalid in (torch.zeros(4096),torch.full((4096,),float('nan'))):
            with self.assertRaises(ValueError):math93.normalize_hidden(invalid)
        for key in ('decode_torch','decode_native','loss','target_xywh','blend_native'):
            self.assertIs(getattr(math93,key),getattr(math84,key))

    def test_actual_warmstart_nonzero_head_Bzero_RNG_and_empty_Adam_are_required(self):
        original,initial=warm_fixture();reg=dict(original84_progress=ref('original_step1'))
        result=review.validate_warmstart(initial,original,reg);self.assertTrue(result['all290_warmstart_tensors_exact'])
        for mode in ('head','rng','moment','B','old_step'):
            a,b=copy.deepcopy(initial),copy.deepcopy(original)
            if mode=='head':a['head_state_dict']['bias'].zero_()
            elif mode=='rng':a['torch_rng_state'][0]=99
            elif mode=='moment':a['optimizer_state_dict']['state']={0:dict(step=1)}
            elif mode=='B':
                key=next(n for n in a['adapter_state_dict'] if '.lora_B.' in n)
                a['adapter_state_dict'][key].fill_(.1);b['adapter_state_dict'][key].fill_(.1)
            else:b['step']=2
            with self.subTest(mode=mode),self.assertRaises(ValueError):review.validate_warmstart(a,b,reg)

    def test_schedule_skips_exact_eight_successes_and_reweights_all602_sources(self):
        old=[dict(id='m'+str(i),source_id='s'+str(i%602),input_id='i'+str(i%602),draw_weight=1.) for i in range(3200)]
        original=dict(train_schedule=old,train_inputs=['compiled602'],screen_inputs=['compiled20'])
        from collections import Counter
        counts=Counter(r['source_id'] for r in old[8:])
        rows=[dict(r,original_micro=i+8,draw_weight=3192/(602*counts[r['source_id']])) for i,r in enumerate(old[8:])]
        prepared=dict(train_schedule=rows,train_inputs=original['train_inputs'],screen_inputs=original['screen_inputs'])
        self.assertEqual(len(review.validate_schedule(prepared,original)),3192)
        prepared['train_schedule'][0]['id']=old[0]['id']
        with self.assertRaises(ValueError):review.validate_schedule(prepared,original)

    def test_new_first_B_and_second_A_gradients_and_original_micro_loss_replay(self):
        updates=[];micros=[];schedule=[];target=dict(source_id='train',original_reference_xywh=[11,17,40,31],width=100,height=80)
        z=[.01,-.02,-.4];loss,parts=math93.loss(torch.tensor(z,dtype=torch.float64),target['original_reference_xywh'],100,80)
        for i in range(16):
            row=dict(id='m'+str(i+8),source_id='train',input_id='input',draw_weight=1.2,original_micro=i+8);schedule.append(row)
            common=dict(step=i//4+1,micro=i,id=row['id'])
            micros.extend([dict(common,event='BEGIN_TRAIN_MICRO',source_id='train'),
                dict(common,event='TRAIN_RAW_LOSS',source_id='train',input_id='input',target_xywh=target['original_reference_xywh'],
                    width=100,height=80,original_micro=i+8,draw_weight=1.2,raw_head=z,unweighted_loss=float(loss),loss=1.2*float(loss),
                    components={k:float(v) for k,v in parts.items()},hidden_retained_real_gradient=True),dict(common,event='TRAIN_BACKWARD_COMPLETE')])
        for step in range(1,5):
            groups={n:dict(tensors=144 if n.startswith('LoRA_') else 1,nonzero_tensors=0 if step==1 and n=='LoRA_A' else 1,
                finite=True,preclip_norm=0. if step==1 and n=='LoRA_A' else 1.) for n in ('LoRA_A','LoRA_B','HEAD_WEIGHT','HEAD_BIAS')}
            updates.append(dict(event='SUCCESSFUL_UPDATE_PERSISTED',step=step,micro=step*4,grad_groups=groups,combined_preclip_gradient_norm=1.))
        result=review.validate_training_journals(updates,micros,schedule,dict(train=target),stage='pilot')
        self.assertTrue(result['first_new_B_nonzero_verified']);self.assertTrue(result['second_new_A_nonzero_verified'])
        updates[0]['grad_groups']['LoRA_B'].update(nonzero_tensors=0,preclip_norm=0.)
        with self.assertRaises(ValueError):review.validate_training_journals(updates,micros,schedule,dict(train=target),stage='pilot')

    def test_CPU_head_replay_uses_original_raw_hidden_then_F32_L2(self):
        source=dict(source_id='s',source_sha256='a'*64,width=100,height=80,pool=[[10,20,60]],baseline_box=[10,20,60],original_BASE_observed=True)
        hidden=torch.linspace(-100,100,4096);head=dict(weight=torch.zeros((3,4096)),bias=torch.tensor([.01,-.01,-.1]))
        head['weight'][0,0]=.1;raw=head['weight']@math93.normalize_hidden(hidden)+head['bias']
        receipt=dict(**{k:source[k] for k in ('source_id','source_sha256','width','height')},adapter_weights=ref('adapter'),head_weights=ref('head'),
            decoded_xyw=math93.decode_torch(raw,100,80).tolist())
        geometry=type('Geometry',(),dict(legal=staticmethod(math84.legal_native)))
        result=review.validate_raw(hidden,raw,receipt,head,source,adapter_weights=ref('adapter'),head_weights=ref('head'),geometry=geometry)
        self.assertTrue(result['raw_hidden_is_original_unnormalized']);self.assertGreater(result['original_hidden_l2_norm'],100.)
        wrong=head['weight']@hidden+head['bias']
        with self.assertRaises(ValueError):review.validate_raw(hidden,wrong,receipt,head,source,adapter_weights=ref('adapter'),head_weights=ref('head'),geometry=geometry)

    def test_full290_checkpoint_counts_new_Adam_steps_and_exact_warmstart(self):
        torch.set_num_threads(2);original,initial=warm_fixture(full=True)
        adapter={n:v+.001 for n,v in initial['adapter_state_dict'].items()};head={n:v+.001 for n,v in initial['head_state_dict'].items()}
        names=[list(adapter),['head.weight','head.bias']];states={};groups=[];index=0
        for gi,ns in enumerate(names):
            ids=[]
            for name in ns:
                value=adapter[name] if gi==0 else head[name.split('.')[1]]
                states[index]=dict(step=torch.tensor(4.),exp_avg=torch.zeros_like(value),exp_avg_sq=torch.zeros_like(value));ids.append(index);index+=1
            groups.append(dict(params=ids,lr=[5e-5,.001][gi],betas=(.9,.999),eps=1e-8,weight_decay=0.))
        reg=dict(original84_progress=ref('old_step1'),recipe=math93.RECIPE,recovery_prepared=ref('recovery'),train_targets=ref('targets'))
        common=dict(original84_progress=reg['original84_progress'],original_successful_updates=1,original_successful_forwards=8,
            optimizer_reset=True,hidden_transform=math93.RECIPE['hidden_transform'])
        progress=dict(schema='DIRECT_BOX_L2_RECOVERY_COMPLETE_UPDATE_PROGRESS_V93',step=4,micro=16,logical_training_forwards=16,
            recipe=math93.RECIPE,no_base_tensors_saved=True,schedule_sha256='a'*64,train_schedule_reference=reg['recovery_prepared'],train_targets_reference=reg['train_targets'],
            adapter_state_dict=adapter,head_state_dict=head,optimizer_parameter_names_by_group=names,optimizer_parameter_names_sha256=review.digest(names),
            optimizer_state_dict=dict(state=states,param_groups=groups),**{k:original[k] for k in ('torch_rng_state','torch_cuda_rng_state_all','numpy_rng_state','python_rng_state')},**common)
        inventory=dict(base=math93.BASE,direct_box_lora=math93.LORA,head=math93.HEAD_PARAMETERS,trainable=math93.LORA+math93.HEAD_PARAMETERS,resident=math93.PHYSICAL,
            pipeline=math93.PIPELINE,actual_lora_matrices=288,actual_language_targets=144,head_tensors=2,adapter='direct_box',original_TIME_loaded=False,old_PAIR_loaded=False,
            old_CROP_loaded=False,old_UTILITY_loaded=False,original_TIME_counted=15335424,semantic_counted=98329)
        done=dict(status='COMPLETE_DIRECT_BOX93_NEW4_ENGINEERING_NO_DEV_MODEL',GPU_registration=ref('reg93'),completed_updates=4,successful_micro=16,
            actual_training_forwards=16,actual_training_forwards_this_phase=16,recipe=math93.RECIPE,train_schedule_reference=reg['recovery_prepared'],train_targets_reference=reg['train_targets'],
            original_TIME_loaded=False,old_PAIR_loaded=False,old_CROP_loaded=False,old_UTILITY_loaded=False,screen_reference_read=False,inventory=inventory,
            base_fingerprint=dict(parameters=math93.BASE,sha256='b'*64),schedule_sha256='a'*64,optimizer_parameter_names_by_group=names,
            optimizer_parameter_names_sha256=review.digest(names),actual_lora_A_changed=True,actual_lora_B_changed=True,progress=ref('progress'),**common)
        result=review.validate_training(done,progress,initial,original,reg,ref('reg93'),stage='pilot',cfg=dict(expected_base_sha256='b'*64))
        self.assertEqual(result['total_adopted_plus_new_updates'],5);self.assertTrue(result['new_optimizer_initially_empty'])
        states[0]['step']=torch.tensor(5.)
        with self.assertRaises(ValueError):review.validate_training(done,progress,initial,original,reg,ref('reg93'),stage='pilot',cfg=dict(expected_base_sha256='b'*64))


if __name__=='__main__':unittest.main()
