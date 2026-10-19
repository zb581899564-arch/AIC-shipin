import copy
import hashlib
import json
from pathlib import Path
import tempfile
from types import SimpleNamespace
import unittest
from unittest import mock

import numpy as np
import torch

import utility_star_gpu_v69 as gpu
import utility_star_math_v68 as math68


def r(name):
    return dict(path='/synthetic/'+name, sha256=hashlib.sha256(name.encode()).hexdigest())


def run_synthetic_screen(root, *, broken_head=False):
    """Real persistence/receipt loop with CPU tiny tensors; no real model/input."""
    root = Path(root); (root/'utility_star_model_69').mkdir()
    inputs_dir = root/'synthetic_inputs'; inputs_dir.mkdir()
    grid = [[1, 2, 2]]*3
    grid_sha = hashlib.sha256(np.asarray(grid, np.int64).tobytes()).hexdigest()
    signature = {k:dict(sha256='a'*64, shape=[1]) for k in ('input_ids', 'attention_mask', 'pixel_values', 'image_grid_thw')}
    signature['image_grid_thw'] = dict(sha256=grid_sha, shape=[3, 3], dtype='torch.int64')
    entries = []; requests = {}
    for i in range(240):
        cid = 'case'+str(i)
        q = dict(id=cid, source_id='owner', source_sha256='a'*64, class_token_ids=[15, 16, 17],
            input_signature=signature, image_grid_thw=grid, reference_or_target_in_prompt=False)
        path = inputs_dir/(cid+'.json'); path.write_text(json.dumps(q), encoding='utf-8')
        entry = dict(id=cid, source_id='owner', input=gpu.ref(path)); entries.append(entry); requests[cid] = q
    values = dict(input_ids=torch.ones((1, 1), dtype=torch.int64), attention_mask=torch.ones((1, 1), dtype=torch.int64),
        pixel_values=torch.zeros((1, 1)), image_grid_thw=torch.tensor(grid))
    calls = []
    def core(**kwargs):
        calls.append(kwargs)
        raw = torch.arange(4096, dtype=torch.float32).reshape(1, 1, 4096)/4096
        return SimpleNamespace(last_hidden_state=raw)
    class Model:
        def eval(self): return self
        def parameters(self): return iter(())
        def get_base_model(self): return SimpleNamespace(model=core)
    head = torch.nn.Linear(4096, 1, bias=False); head.weight.data.fill_(.001); head.requires_grad_(False)
    if broken_head:
        def forward(_): raise RuntimeError('synthetic head failure after persistence')
        head.forward = forward
    beta = torch.zeros(11)
    def tensor_file(path, value, _):
        with Path(path).open('xb') as stream: torch.save(value, stream)
    frozen = SimpleNamespace(_deadline=lambda _:None, _input=lambda _, e, *a, **kw:(values, requests[e['id']]), _tensor_file=tensor_file)
    original_to = torch.Tensor.to
    def to_cpu(self, *args, **kwargs):
        return self if args and args[0] == 'cuda:0' else original_to(self, *args, **kwargs)
    successful = []
    with mock.patch.object(gpu, 'utility', math68), mock.patch.object(gpu, 'bound', side_effect=lambda ref:Path(ref['path'])), \
         mock.patch.object(torch.Tensor, 'to', to_cpu), mock.patch.object(torch.cuda, 'synchronize'):
        completion = gpu._ordered_screen(root, Model(), head, beta, None, entries, {}, r('reg'), r('adapter'), r('value'),
            frozen, torch, successful)
    return completion, entries, dict(weight=head.weight.detach().cpu().clone(), geometry_beta=beta), calls


class StarGPUTests(unittest.TestCase):
    def test_global_schedule_boundary_and_fixed_steps(self):
        self.assertEqual(gpu.schedule_index(2000), 0)
        self.assertEqual(gpu.schedule_index(5199), 3199)
        self.assertEqual(list(math68.phase_steps('pilot4')), [501, 502, 503, 504])
        self.assertEqual(len(math68.phase_steps('remaining796')), 796)
        for bad in (1999, 5200, True):
            with self.assertRaises(ValueError): gpu.schedule_index(bad)

    def test_inheritance_cannot_initialize_or_replay_old_steps(self):
        reg = dict(prepared=r('prepared68'), old55_progress=r('old500'))
        prepared = dict(train_target_RMS=math68.TARGET_RMS)
        old_recipe = dict(updates=500)
        old = dict(schema='UTILITY_R8_COMPLETE_UPDATE_PROGRESS_V55', step=500, micro=2000, logical_training_forwards=4000,
            train_target_RMS=math68.TARGET_RMS, recipe=old_recipe, original_TIME_loaded=False, old_PAIR_loaded=False,
            old_CROP_loaded=False, no_base_tensors_saved=True)
        with mock.patch.object(gpu, 'utility', math68):
            self.assertEqual(gpu.validate_resume_contract(old, reg, prepared, 'sha68', 'pilot4', old_recipe), 500)
            bad = dict(old, step=0)
            with self.assertRaises(ValueError): gpu.validate_resume_contract(bad, reg, prepared, 'sha68', 'pilot4', old_recipe)
            new = dict(old, schema='UTILITY_STAR_COMPLETE_UPDATE_PROGRESS_V69', step=504, micro=2016,
                logical_training_forwards=4032, recipe=math68.RECIPE, schedule_sha256='sha68',
                train_schedule_reference=reg['prepared'], inherited_progress=reg['old55_progress'],
                new_updates=4, new_micro=16, new_training_forwards=32)
            self.assertEqual(gpu.validate_resume_contract(new, reg, prepared, 'sha68', 'remaining796', old_recipe), 504)
            for change in (dict(step=503), dict(inherited_progress=r('wrong')), dict(train_target_RMS=.2)):
                with self.assertRaises(ValueError): gpu.validate_resume_contract(dict(new, **change), reg, prepared, 'sha68', 'remaining796', old_recipe)

    def test_value_gradients_and_exact_swap_selfzero(self):
        head = torch.nn.Linear(4096, 1, bias=False); head.weight.data.fill_(.001)
        forward = torch.ones(4096, requires_grad=True); reverse = torch.zeros(4096, requires_grad=True)
        beta = torch.nn.Parameter(torch.ones(11)*.01); geom = torch.ones(11)
        g = gpu._prediction(head, forward, reverse, beta, geom)
        self.assertTrue(torch.equal(gpu._prediction(head, reverse, forward, beta, -geom), -g))
        self.assertEqual(float(gpu._prediction(head, forward, forward, beta, geom*0)), 0.)
        g.backward()
        self.assertTrue(all(v is not None and bool(torch.count_nonzero(v)) for v in
            (forward.grad, reverse.grad, head.weight.grad, beta.grad)))

    def test_new_role_aliases_once_and_raw_survives_head_failure(self):
        with tempfile.TemporaryDirectory() as temp:
            complete, _, _, calls = run_synthetic_screen(temp)
            done = gpu.read(complete['path'])
            self.assertEqual(len(calls), 1)
            self.assertEqual((done['actual_forward_calls'], done['aliases']), (1, 239))
            self.assertEqual(done['model_role'], 'UTILITY_STAR_TRAINED_screen')
        with tempfile.TemporaryDirectory() as temp:
            with self.assertRaisesRegex(RuntimeError, 'head failure'):
                run_synthetic_screen(temp, broken_head=True)
            stage = Path(temp)/'utility_star_model_69/TRAINED_screen'
            self.assertTrue((stage/'0000.hidden.pt').is_file())
            self.assertFalse((stage/'0000.receipt.json').exists())
            self.assertFalse((stage/'completion.json').exists())


if __name__ == '__main__': unittest.main()
