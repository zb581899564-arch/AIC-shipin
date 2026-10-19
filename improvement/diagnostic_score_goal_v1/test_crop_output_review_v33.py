import copy
import random
import unittest
import numpy as np
import torch
from crop_output_review_v33 import validate_raw,validate_alias,validate_logs,validate_progress,_same_state,RECIPE


class RawTests(unittest.TestCase):
    def test_full_vocab_independent_three_class_softmax_and_failures(self):
        raw=torch.tensor([100.,1.,2.,3.,-100.]);ids=[1,2,3];logits=raw[ids].double();p=torch.softmax(logits,0)
        r=dict(full_vocabulary_size=5,class_token_ids=ids,raw_dtype='torch.float32',class_logits=logits.tolist(),probabilities=p.tolist(),predicted_index=2)
        np.testing.assert_array_equal(validate_raw(raw,r,ids,5),p.numpy())
        for bad in (raw[:4],raw.half(),raw*float('nan')):
            with self.assertRaises(ValueError):validate_raw(bad,r,ids,5)
        bad=dict(r,probabilities=[.1,.2,.7])
        with self.assertRaises(ValueError):validate_raw(raw,bad,ids,5)
        with self.assertRaises(ValueError):validate_raw(raw,r,[0,2,3],5)

    def test_alias_source_role_and_classes_and_repeat_protection(self):
        r=dict(model_role='BASE_screen',source_id='x',source_sha256='a'*64,class_token_ids=[1,2,3],input_signature={'x':'same'},
            raw_logits=dict(path='raw',sha256='r'),actual_new_forward=True,alias_of=None)
        first=dict(path='r1',sha256='1');second=dict(path='r2',sha256='2');key=validate_alias(r,first,{},set())
        old={'r1':dict(reference=first,receipt=r)};alias=dict(r,actual_new_forward=False,alias_of=first)
        self.assertEqual(validate_alias(alias,second,old,{key}),key)
        for changed in (dict(source_id='y'),dict(source_sha256='b'*64),dict(model_role='TRAINED_screen'),dict(class_token_ids=[0,2,3])):
            with self.assertRaises(ValueError):validate_alias(dict(alias,**changed),second,old,{key})
        with self.assertRaises(ValueError):validate_alias(r,second,old,{key})

    def test_byte_exact_state_check_rejects_signed_zero_and_dtype(self):
        self.assertTrue(_same_state({'x':torch.zeros(1)},{'x':torch.zeros(1)},torch))
        self.assertFalse(_same_state({'x':torch.tensor([-0.])},{'x':torch.tensor([0.])},torch))
        self.assertFalse(_same_state({'x':torch.zeros(1,dtype=torch.float16)},{'x':torch.zeros(1)},torch))


class TrainingJournalTests(unittest.TestCase):
    def fixture(self):
        schedule=[dict(id='T'+str(i),source_id='s'+str(i),input=dict(path='i'+str(i),sha256='x'))for i in range(16)]
        requests={r['input']['path']:dict(id='stable'+str(i),source_id=r['source_id'])for i,r in enumerate(schedule)}
        updates=[dict(event='SUCCESSFUL_UPDATE_PERSISTED',step=i,micro=4*i,mean_micro_loss=1.,preclip_gradient_norm=.1,
            finite_gradient_matrices=288,nonzero_gradient_matrices=144,progress_sha256='last'if i==4 else'sha')for i in range(1,5)]
        events=[]
        for i,row in enumerate(schedule):
            common=dict(step=i//4+1,micro=i,id=row['id'])
            events.extend([dict(common,event='BEGIN_TRAIN_MICRO',request_id=requests[row['input']['path']]['id'],source_id=row['source_id'],input=row['input']),
                dict(common,event='TRAIN_RAW_LOSS',request_id=requests[row['input']['path']]['id'],source_id=row['source_id'],class_token_ids=[1,2,3],loss=1.,softmax_scope='THREE_CLASSES_ONLY'),
                dict(common,event='TRAIN_BACKWARD_COMPLETE')])
        return updates,events,schedule,requests

    def test_exact16_micro_and_first_update_zero_A_grad_allowed(self):
        u,m,s,r=self.fixture();out=validate_logs(u,m,s,1,4,'last',[1,2,3],r)
        self.assertEqual(out['successful_updates'],4);self.assertEqual(out['successful_micro'],16)

    def test_missing_micro_nonfinite_zero_grad_wrong_schedule_and_progress_rejected(self):
        u,m,s,r=self.fixture()
        with self.assertRaises(ValueError):validate_logs(u,m[:-1],s,1,4,'last',[1,2,3],r)
        for changes in (dict(preclip_gradient_norm=0.),dict(nonzero_gradient_matrices=0),dict(mean_micro_loss=float('nan'))):
            bad=copy.deepcopy(u);bad[0].update(changes)
            with self.assertRaises(ValueError):validate_logs(bad,m,s,1,4,'last',[1,2,3],r)
        with self.assertRaises(ValueError):validate_logs(u,m,s,1,4,'wrong',[1,2,3],r)
        bad=copy.deepcopy(m);bad[0]['request_id']='wrong'
        with self.assertRaises(ValueError):validate_logs(u,bad,s,1,4,'last',[1,2,3],r)


class ProgressTests(unittest.TestCase):
    def test_actual288_crop_shapes_adam4_rng_and_stale_state_rejection(self):
        torch.set_num_threads(2)
        weights={};moments={}
        for layer in range(36):
            for projection in ('q_proj','k_proj','v_proj','o_proj'):
                for kind,shape in (('A',(8,4096)),('B',((4096 if projection in ('q_proj','o_proj') else 1024),8))):
                    key=f'base_model.model.model.language_model.layers.{layer}.self_attn.{projection}.lora_{kind}.weight'
                    weights[key]=torch.zeros(shape)
                    moments[len(moments)]=dict(step=torch.tensor(4.),exp_avg=torch.zeros(shape),exp_avg_sq=torch.zeros(shape))
        rng=np.random.RandomState(0).get_state();prepared=dict(path='prepared',sha256='p')
        state=dict(schema='CROP_R8_COMPLETE_UPDATE_PROGRESS_V1',step=4,micro=16,schedule_sha256='s',train_schedule_reference=prepared,
            recipe=RECIPE,original_TIME_loaded=False,old_PAIR_loaded=False,no_base_tensors_saved=True,adapter_state_dict=weights,
            optimizer_state_dict=dict(param_groups=[dict(lr=5e-5,weight_decay=0.,params=list(moments))],state=moments),
            torch_rng_state=torch.Generator().get_state(),torch_cuda_rng_state_all=[torch.zeros(16,dtype=torch.uint8)],
            numpy_rng_state=dict(name=rng[0],keys=torch.tensor(rng[1].astype(np.int64)),position=rng[2],has_gauss=rng[3],cached_gaussian=rng[4]),
            python_rng_state=random.Random(0).getstate())
        result=validate_progress(state,4,'s',prepared)
        self.assertEqual(result['matrices'],288);self.assertEqual(result['parameters'],7667712)
        self.assertEqual(result['adam_states'],288)
        moments[0]['step']=torch.tensor(3.)
        with self.assertRaises(ValueError):validate_progress(state,4,'s',prepared)
        moments[0]['step']=torch.tensor(4.)
        state['torch_rng_state']=torch.ones(4,dtype=torch.float32)
        with self.assertRaises(ValueError):validate_progress(state,4,'s',prepared)


if __name__=='__main__':unittest.main()
