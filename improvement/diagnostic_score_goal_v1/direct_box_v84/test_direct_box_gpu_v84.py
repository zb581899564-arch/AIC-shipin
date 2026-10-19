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

import direct_box_gpu_v84 as gpu
import direct_box_math_v84 as math84


def r(name):
    return dict(path='/synthetic/'+name, sha256='a'*64)


def values_and_request(identifier='i', source='s', sha='a'*64, role='screen'):
    values = dict(input_ids=torch.ones((1, 8), dtype=torch.int64), attention_mask=torch.ones((1, 8), dtype=torch.int64),
        pixel_values=torch.zeros((4, 1536), dtype=torch.float32), image_grid_thw=torch.tensor([[1, 2, 2]], dtype=torch.int64))
    request = dict(id=identifier, source_id=source, source_sha256=sha, role=role, width=160, height=100,
        reference_or_target_in_prompt=False, input_signature=gpu.signature(values), image_grid_thw=[[1, 2, 2]])
    return values, request


def synthetic_screen(root, *, fail_head=False):
    root = Path(root); (root/'direct_box_model_84').mkdir()
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


class DirectBoxRuntimeTests(unittest.TestCase):
    @classmethod
    def setUpClass(cls): torch.set_num_threads(2)

    def test_explicit_reader87_registration_and_accepted_pilot_required(self):
        with tempfile.TemporaryDirectory() as temp:
            root = Path(temp).resolve()
            def ref(path): return dict(path=str(Path(path).resolve()), sha256='a'*64)
            regpath = root/'direct_box_GPU_registration_84.json'
            reg = {name:ref(root/(name+'.json')) for name in gpu.GPU_REFS}
            reg.update(schema=gpu.SCHEMA, GPU_code=ref(Path(gpu.__file__).resolve()), recipe=math84.RECIPE,
                CPU_registration=ref(root/'direct_box_CPU_registration_87.json'),
                prepared=ref(root/'direct_box_inputs_84/prepared.json'), input_acceptance=ref(root/'direct_box_inputs_84/input_acceptance.json'))
            remaining = dict(schema=gpu.REMAINING_SCHEMA, original_GPU_registration=ref(regpath), expected_remaining_updates=796,
                pilot_output_acceptance=ref(root/'pilotQA.json'), pilot_completion=ref(root/'pilot.json'), immutable_pilot_progress=ref(root/'pilot_progress.pt'),
                **{k:reg[k] for k in ('GPU_code','math_code','prepared','input_acceptance')})
            accepted = dict(status='PASS_DIRECT_BOX84_PILOT4_FIRST_ENGINEERING_QA', registration=ref(regpath),
                pilot_completion=remaining['pilot_completion'], engineering=dict(progress=remaining['immutable_pilot_progress'],global_updates=4))
            old32 = {k:reg[k] for k in ('model_config','old_TIME','old_PAIR','original_GPU18')}
            old32['GPU_code'] = ref(root/'old32gpu.py')
            docs = {str(regpath):reg,
                reg['input_acceptance']['path']:dict(status=gpu.INPUT_GATE,prepared=reg['prepared'],registration=reg['CPU_registration']),
                reg['original_GPU32']['path']:old32,
                reg['original_GPU18']['path']:dict(runtime_dependencies=[],pair_registration=ref(root/'old17.json')),
                str(root/'old17.json'):dict(new_code={}), str(root/'direct_box_remaining_admission_84.json'):remaining,
                str(root/'pilotQA.json'):accepted}
            frozen = SimpleNamespace(_deadline=lambda _:None)
            with mock.patch.object(gpu,'bound',side_effect=lambda x:Path(x['path'])), \
                 mock.patch.object(gpu,'read',side_effect=lambda p:docs[str(p)]), mock.patch.object(gpu,'ref',side_effect=ref), \
                 mock.patch.object(gpu,'module',side_effect=[math84,frozen,math84,frozen]):
                got = gpu._registration(root,'remaining796')
                self.assertEqual(got[0]['CPU_registration'],reg['CPU_registration'])
                accepted['engineering']['global_updates'] = 0
                with self.assertRaises(ValueError): gpu._registration(root,'remaining796')

    def test_phase_and_source_equal_schedule_single_forward_counts(self):
        train = [dict(id='t'+str(i), source_id='t'+str(i), source_sha256=f'{i:064x}', role='train', input=r('t'+str(i))) for i in range(602)]
        screen = [dict(id='s'+str(i), source_id='s'+str(i), source_sha256=f'{i+602:064x}', role='screen', input=r('s'+str(i))) for i in range(20)]
        rows = []
        for i in range(3200):
            entry = train[i%602]; count = 6 if i%602 < 190 else 5
            rows.append(dict(id='D'+str(i), source_id=entry['source_id'], source_sha256=entry['source_sha256'], input_id=entry['id'], input=entry['input'], draw_weight=3200/(602*count)))
        prepared = dict(schema='DIRECT_BOX_SOURCE_ONLY_INPUTS_V84', train_inputs=train, screen_inputs=screen, train_schedule=rows, schedule_sha256=gpu.digest(rows))
        _, _, _, report = gpu.validate_schedule(prepared)
        self.assertEqual(report['micro'], 3200)
        self.assertEqual(list(gpu.phase_steps('pilot4')), [1, 2, 3, 4])
        self.assertEqual(len(gpu.phase_steps('remaining796')), 796)
        bad = copy.deepcopy(prepared); bad['train_schedule'][0]['draw_weight'] = 1.
        with self.assertRaises(ValueError): gpu.validate_schedule(bad)
        bad = copy.deepcopy(prepared); bad['screen_inputs'][0]['source_sha256'] = train[0]['source_sha256']
        with self.assertRaises(ValueError): gpu.validate_schedule(bad)

    def test_source_only_input_owner_grid_and_no_target_guard(self):
        values, q = values_and_request()
        entry = dict(id='i', source_id='s', source_sha256='a'*64, role='screen', input=r('i'))
        reader = SimpleNamespace(get=lambda _: (values, q))
        self.assertEqual(gpu._input(reader, entry, torch)[1]['id'], 'i')
        q['original_reference_xywh'] = [0, 0, 10, 10]
        with self.assertRaises(ValueError): gpu._input(reader, entry, torch)
        del q['original_reference_xywh']; q['source_sha256'] = 'b'*64
        with self.assertRaises(ValueError): gpu._input(reader, entry, torch)
        q['source_sha256'] = 'a'*64; values['image_grid_thw'] = torch.tensor([[1, 2, 2]]*3)
        q['input_signature'] = gpu.signature(values); q['image_grid_thw'] = values['image_grid_thw'].tolist()
        with self.assertRaises(ValueError): gpu._input(reader, entry, torch)

    def test_zero_head_gradient_warmup_real_autograd_and_original_xywh_loss(self):
        torch.manual_seed(20261018)
        a = torch.nn.Parameter(torch.ones((4, 8))*.05); b = torch.nn.Parameter(torch.zeros((8, 4)))
        head = torch.nn.Linear(8, 3, bias=True); head.weight.data.zero_(); head.bias.data.zero_()
        params = [('toy.lora_A.direct_box.weight', a), ('toy.lora_B.direct_box.weight', b)]
        optimizer = torch.optim.AdamW([dict(params=[a, b], lr=5e-5), dict(params=list(head.parameters()), lr=.001)], weight_decay=0.)
        source = torch.arange(1, 9, dtype=torch.float32)/8
        for step in range(1, 5):
            optimizer.zero_grad(set_to_none=True)
            hidden = source+b@(a@source)
            raw = head(hidden)
            loss, _ = math84.loss(raw, [20., 20., 100., 40.], 160, 100)  # Original target is not forced16:9.
            loss.backward(); groups = gpu._gradient_groups(params, head, torch)
            gpu.validate_pilot_gradients(groups, step)
            if step == 1:
                self.assertEqual(groups['LoRA_A']['nonzero_tensors'], 0)
                self.assertEqual(groups['LoRA_B']['nonzero_tensors'], 0)
                bad = copy.deepcopy(groups); bad['HEAD_BIAS'].update(nonzero_tensors=0, preclip_norm=0.)
                with self.assertRaises(ValueError): gpu.validate_pilot_gradients(bad, 1)
            optimizer.step()
        self.assertGreater(int(torch.count_nonzero(a.detach()-.05)), 0)
        self.assertGreater(int(torch.count_nonzero(b)), 0)

    def test_complete_two_group290_adam_and_rng_checkpoint_serialization(self):
        matrices = [torch.nn.Parameter(torch.ones(1)) for _ in range(288)]
        head = torch.nn.Linear(4096, 3, bias=True)
        optimizer = torch.optim.AdamW([dict(params=matrices, lr=5e-5), dict(params=list(head.parameters()), lr=.001)], weight_decay=0.)
        for _ in range(4):
            for p in matrices+list(head.parameters()): p.grad = torch.ones_like(p)
            optimizer.step(); optimizer.zero_grad(set_to_none=True)
        trainables = dict(adapter_state_dict={'p'+str(i):p.detach().clone() for i, p in enumerate(matrices)}, head_state_dict={k:v.detach().clone() for k, v in head.state_dict().items()})
        names = [list(trainables['adapter_state_dict']), ['head.weight', 'head.bias']]
        def cpu_tree(value, _):
            if isinstance(value, torch.Tensor): return value.detach().cpu().clone()
            if isinstance(value, dict): return {k:cpu_tree(v, _) for k, v in value.items()}
            if isinstance(value, list): return [cpu_tree(v, _) for v in value]
            if isinstance(value, tuple): return tuple(cpu_tree(v, _) for v in value)
            return value
        frozen = SimpleNamespace(_cpu_tree=cpu_tree)
        reg = dict(prepared=r('prepared'), train_targets=r('train_targets'), recipe=math84.RECIPE)
        with mock.patch.object(gpu, '_trainables', return_value=trainables), mock.patch.object(torch.cuda, 'get_rng_state_all', return_value=[torch.zeros(16, dtype=torch.uint8)]):
            state = gpu._progress(None, head, optimizer, torch, np, frozen, 4, 'schedule', reg, names)
        self.assertEqual(len(state['optimizer_state_dict']['state']), 290)
        self.assertEqual([len(g['params']) for g in state['optimizer_state_dict']['param_groups']], [288, 2])
        self.assertEqual(state['logical_training_forwards'], 16)
        self.assertEqual(state['train_targets_reference'], reg['train_targets'])
        random.Random().setstate(state['python_rng_state'])
        n = state['numpy_rng_state']; np.random.RandomState().set_state((n['name'], n['keys'].numpy().astype(np.uint32), n['position'], n['has_gauss'], n['cached_gaussian']))
        with tempfile.TemporaryDirectory() as temp:
            path = Path(temp)/'progress.pt'; torch.save(state, path)
            loaded = torch.load(path, map_location='cpu', weights_only=True)
            self.assertTrue(gpu._tree_equal(state, loaded, torch))
        for moment in state['optimizer_state_dict']['state'].values(): self.assertEqual(float(moment['step']), 4.)

    def test_final20_persisted_hidden_head_owner_and_head_failure_preservation(self):
        with tempfile.TemporaryDirectory() as temp:
            reference, calls = synthetic_screen(temp)
            done = gpu.read(reference['path'])
            self.assertEqual(len(calls), 20)
            self.assertEqual((done['actual_forward_calls'], done['aliases']), (20, 0))
            self.assertEqual(done['status'], gpu.SCREEN_STATUS)
            receipt = gpu.read(done['entries'][0]['receipt']['path'])
            self.assertEqual(receipt['model_role'], gpu.ROLE)
            self.assertEqual(tuple(torch.load(receipt['raw_hidden']['path'], weights_only=True).shape), (4096,))
            self.assertEqual(tuple(torch.load(receipt['raw_head']['path'], weights_only=True).shape), (3,))
            events = [json.loads(line)['event'] for line in Path(done['attempts']['path']).read_text().splitlines()]
            self.assertEqual(events[:3], ['BEGIN_NEW_ROLE_FORWARD', 'FIRST_RAW_PERSISTED', 'ACCEPTED_NEW_ROLE_RESULT'])
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, 'synthetic head failure'): synthetic_screen(temp, fail_head=True)
            stage = Path(temp)/'direct_box_model_84/TRAINED_screen'
            self.assertTrue((stage/'0000.hidden.pt').exists())
            self.assertFalse((stage/'0000.receipt.json').exists())
            self.assertFalse((stage/'completion.json').exists())


if __name__ == '__main__': unittest.main()
