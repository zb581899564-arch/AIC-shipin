import copy
import json
import os
from pathlib import Path
import random
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

import direct_box_gpu_recovery_v93 as gpu
import direct_box_math_recovery_v93 as math84


def r(name):
    return dict(path='/synthetic/'+name, sha256='a'*64)


def values_and_request(identifier='i', source='s', sha='a'*64, role='screen'):
    values = dict(input_ids=torch.ones((1, 8), dtype=torch.int64), attention_mask=torch.ones((1, 8), dtype=torch.int64),
        pixel_values=torch.zeros((4, 1536), dtype=torch.float32), image_grid_thw=torch.tensor([[1, 2, 2]], dtype=torch.int64))
    request = dict(id=identifier, source_id=source, source_sha256=sha, role=role, width=160, height=100,
        reference_or_target_in_prompt=False, input_signature=gpu.signature(values), image_grid_thw=[[1, 2, 2]])
    return values, request


def synthetic_screen(root, *, fail_head=False):
    root = Path(root); (root/'direct_box_model_93').mkdir()
    input_dir = root/'synthetic'; input_dir.mkdir()
    entries = []; payload = {}
    for i in range(20):
        cid, sid, sha = 'i'+str(i), 's'+str(i), f'{i:064x}'
        values, q = values_and_request(cid, sid, sha)
        path = input_dir/(cid+'.json'); path.write_text(json.dumps(q), encoding='utf-8')
        reference = gpu.ref(path)
        entries.append(dict(id=cid, source_id=sid, source_sha256=sha, role='screen', input=reference))
        payload[str(path)] = values, q
    prepared_path = root/'direct_box_inputs_84'; prepared_path.mkdir()
    prepared = dict(screen_inputs=entries); (prepared_path/'prepared.json').write_text(json.dumps(prepared), encoding='utf-8')
    calls = []
    def core(**values):
        calls.append(values)
        return SimpleNamespace(last_hidden_state=torch.arange(4096, dtype=torch.float32).reshape(1, 1, 4096)/4096)
    class Model:
        def eval(self): return self
        def parameters(self): return iter(())
        def get_base_model(self): return SimpleNamespace(model=core)
    head = torch.nn.Linear(4096, 3, bias=True); head.weight.data.zero_(); head.bias.data.zero_(); head.requires_grad_(False)
    if fail_head:
        def broken(_): raise RuntimeError('synthetic head failure')
        head.forward = broken
    reader = SimpleNamespace(get=lambda ref:payload[ref['path']])
    def save_tensor(path, value, _):
        with Path(path).open('xb') as handle:
            torch.save(value, handle); handle.flush(); os.fsync(handle.fileno())
    frozen = SimpleNamespace(_deadline=lambda _:None, _tensor_file=save_tensor)
    successful = []; original_to = torch.Tensor.to
    def to_cpu(self, *args, **kwargs):
        return self if args and args[0] == 'cuda:0' else original_to(self, *args, **kwargs)
    with mock.patch.object(torch.Tensor, 'to', to_cpu), mock.patch.object(torch.cuda, 'synchronize'):
        result = gpu._screen(root, Model(), head, reader, prepared, {}, r('GPUreg'), r('adapter'), r('head'), math84,
            frozen, torch, successful)
    return result, calls


class RecoveryRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): torch.set_num_threads(2)

    def test_schedule_skip8_reweight602_and_exact_new798(self):
        train=[dict(id='I'+str(i),source_id='S'+str(i),source_sha256=f'{i:064x}',role='train',input=r('I'+str(i))) for i in range(602)]
        screen=[dict(id='Q'+str(i),source_id='Q'+str(i),source_sha256=f'{i+1000:064x}',role='screen',input=r('Q'+str(i))) for i in range(20)]
        rows=[]
        for i in range(3200):
            e=train[i%602]; n=6 if i%602<190 else 5
            rows.append(dict(id='D'+str(i),source_id=e['source_id'],source_sha256=e['source_sha256'],input_id=e['id'],input=e['input'],draw_weight=3200/(602*n)))
        prepared=dict(schema='DIRECT_BOX_SOURCE_ONLY_INPUTS_V84',train_inputs=train,screen_inputs=screen,train_schedule=rows,schedule_sha256=gpu.digest(rows))
        counts=gpu.Counter(row['source_id'] for row in rows[8:])
        new=[dict(row,draw_weight=3192/(602*counts[row['source_id']]),original_micro=i+8) for i,row in enumerate(rows[8:])]
        recovery=dict(schema='DIRECT_BOX_L2_RECOVERY_SCHEDULE_V93',original_prepared=r('prepared'),original_schedule_sha256=prepared['schedule_sha256'],skipped_original_micro_indices=list(range(8)),train_schedule=new,schedule_sha256=gpu.digest(new))
        got,_,_,_=gpu.validate_schedule(prepared,recovery,r('prepared'))
        self.assertEqual([got[0]['original_micro'],got[-1]['original_micro']],[8,3199])
        self.assertEqual(len(got),3192); self.assertEqual(len(gpu.phase_steps('remaining794')),794)
        self.assertEqual(list(gpu.phase_steps('remaining794'))[-1],798)
        weights=gpu.Counter()
        for row in got: weights[row['source_id']]+=row['draw_weight']/3192
        self.assertTrue(all(abs(w-1/602)<1e-15 for w in weights.values()))
        bad=copy.deepcopy(recovery); bad['train_schedule'][0]['original_micro']=0
        with self.assertRaises(ValueError): gpu.validate_schedule(prepared,bad,r('prepared'))

    def test_nonzero_adopted_head_B_first_A_second_real_autograd(self):
        torch.manual_seed(20261018)
        a=torch.nn.Parameter(torch.randn(8,4096)*.01); b=torch.nn.Parameter(torch.zeros(4096,8))
        head=torch.nn.Linear(4096,3)
        with torch.no_grad():
            head.weight.copy_(torch.randn_like(head.weight)*.001)
            head.bias.copy_(torch.tensor([-.001,.001,-.01]))
        params=[('toy.lora_A.direct_box.weight',a),('toy.lora_B.direct_box.weight',b)]
        opt=torch.optim.AdamW([dict(params=[a,b],lr=5e-5),dict(params=list(head.parameters()),lr=.001)],weight_decay=0.)
        source=torch.randn(4096)
        for step in range(1,5):
            opt.zero_grad(set_to_none=True); h=source+b@(a@source)
            loss,_=math84.loss(head(math84.normalize_hidden(h)),[20.,20.,100.,40.],160,100)
            loss.backward(); groups=gpu._gradient_groups(params,head,torch)
            gpu.validate_pilot_gradients(groups,step); opt.step()
        self.assertGreater(int(torch.count_nonzero(b)),0)
        bad=copy.deepcopy(groups); bad['LoRA_A'].update(nonzero_tensors=0,preclip_norm=0.)
        with self.assertRaises(ValueError): gpu.validate_pilot_gradients(bad,2)

    def test_L2_gradient_scale_bound_and_no_zero_fallback(self):
        h=torch.arange(1,4097,dtype=torch.float32,requires_grad=True)
        normalized=math84.normalize_hidden(h)
        self.assertAlmostEqual(float(normalized.detach().norm()),1.,places=6)
        self.assertTrue(torch.equal(normalized,math84.normalize_hidden(h*64)))
        normalized[0].backward(); self.assertGreater(float(h.grad.norm()),0.)
        with self.assertRaises(ValueError): math84.normalize_hidden(torch.zeros(4096))
        head=torch.nn.Linear(4096,3); head.weight.data.fill_(.001); head.bias.data.fill_(.001)
        self.assertTrue(bool((head(normalized.detach()).abs() <= head.weight.norm(dim=1)+head.bias.abs()).all()))

    def test_only_step1_allBzero_warmstart_accepted(self):
        keys=[f'layer{i}.lora_{kind}.weight' for i in range(144) for kind in ('A','B')]
        names=[keys,['head.weight','head.bias']]
        original=dict(prepared=r('prepared'),train_targets=r('targets'),recipe={'old':84})
        warm=dict(schema='DIRECT_BOX_COMPLETE_UPDATE_PROGRESS_V84',step=1,micro=4,logical_training_forwards=4,
            schedule_sha256='s',train_schedule_reference=original['prepared'],train_targets_reference=original['train_targets'],recipe=original['recipe'],
            optimizer_parameter_names_by_group=names,optimizer_parameter_names_sha256=gpu.digest(names),
            adapter_state_dict={k:torch.zeros(1) if '.lora_B.' in k else torch.ones(1) for k in keys},
            head_state_dict=dict(weight=torch.full((3,4096),.001),bias=torch.full((3,),.001)),
            optimizer_state_dict=dict(state={i:{'step':torch.tensor(1.)} for i in range(290)},param_groups=[dict(params=list(range(288))),dict(params=[288,289])]),
            **{key:None for key in gpu.RNG_KEYS})
        gpu.validate_warmstart(warm,original,dict(schedule_sha256='s'),names,torch)
        bad=copy.deepcopy(warm); bad['step']=2
        with self.assertRaises(ValueError): gpu.validate_warmstart(bad,original,dict(schedule_sha256='s'),names,torch)
        bad=copy.deepcopy(warm); bad['adapter_state_dict'][keys[1]].fill_(1)
        with self.assertRaises(ValueError): gpu.validate_warmstart(bad,original,dict(schedule_sha256='s'),names,torch)

    def test_initial_progress_proves_empty_Adam_and_serializable_four_RNG(self):
        matrices=[torch.nn.Parameter(torch.ones(1)) for _ in range(288)]
        head=torch.nn.Linear(4096,3)
        optimizer=torch.optim.AdamW([dict(params=matrices,lr=5e-5),dict(params=list(head.parameters()),lr=.001)],weight_decay=0.)
        trainables=dict(adapter_state_dict={'p'+str(i):p.detach().clone() for i,p in enumerate(matrices)},
            head_state_dict={k:v.detach().clone() for k,v in head.state_dict().items()})
        names=[list(trainables['adapter_state_dict']),['head.weight','head.bias']]
        reg=dict(prepared=r('oldprepared'),recovery_prepared=r('new3192'),train_targets=r('targets'),original84_progress=r('warm84'),recipe=math84.RECIPE)
        frozen=SimpleNamespace(_cpu_tree=lambda value,_:copy.deepcopy(value))
        with mock.patch.object(gpu,'_trainables',return_value=trainables), mock.patch.object(torch.cuda,'get_rng_state_all',return_value=[torch.zeros(16,dtype=torch.uint8)]):
            state=gpu._progress(None,head,optimizer,torch,np,frozen,0,'newSHA',reg,names)
        self.assertEqual(state['optimizer_state_dict']['state'],{})
        self.assertEqual([len(g['params']) for g in state['optimizer_state_dict']['param_groups']],[288,2])
        self.assertEqual(state['train_schedule_reference'],reg['recovery_prepared'])
        self.assertEqual((state['step'],state['micro'],state['original_successful_forwards']),(0,0,8))
        self.assertTrue(all(key in state for key in gpu.RNG_KEYS))
        with tempfile.TemporaryDirectory() as temp:
            path=Path(temp)/'initial.pt';torch.save(state,path)
            self.assertTrue(gpu._tree_equal(state,torch.load(path,map_location='cpu',weights_only=True),torch))

    def test_screen20_and_head_failure_keep_first_hidden(self):
        with tempfile.TemporaryDirectory() as temp:
            reference,calls=synthetic_screen(temp); done=gpu.read(reference['path'])
            self.assertEqual(done['status'],gpu.SCREEN_STATUS)
            self.assertEqual((len(calls),done['actual_forward_calls'],done['aliases']),(20,20,0))
            receipt=gpu.read(done['entries'][0]['receipt']['path'])
            self.assertEqual(receipt['model_role'],'DIRECT_BOX93_TRAINED_screen')
            h=torch.load(receipt['raw_hidden']['path'],weights_only=True)
            self.assertFalse(torch.isclose(h.norm(),torch.tensor(1.)))
            events=[json.loads(line)['event'] for line in Path(done['attempts']['path']).read_text().splitlines()]
            self.assertEqual(events[:3],['BEGIN_NEW_ROLE_FORWARD','FIRST_RAW_PERSISTED','ACCEPTED_NEW_ROLE_RESULT'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError,'synthetic head failure'): synthetic_screen(temp,fail_head=True)
            stage=Path(temp)/'direct_box_model_93/TRAINED_screen'
            self.assertTrue((stage/'0000.hidden.pt').is_file()); self.assertFalse((stage/'completion.json').exists())


if __name__=='__main__': unittest.main()


